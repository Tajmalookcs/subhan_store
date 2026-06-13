from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from apps.products.models import Product, Category, Brand, ProductReview
from .models import Cart, CartItem, Wishlist


# ── Helpers ────────────────────────────────────────────────────────────────

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    # Guest cart via session
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart


def merge_guest_cart(request):
    """Merge guest session cart into user cart after login."""
    if not request.session.session_key:
        return
    guest_cart = Cart.objects.filter(
        session_key=request.session.session_key, user=None
    ).first()
    if not guest_cart:
        return
    user_cart, _ = Cart.objects.get_or_create(user=request.user)
    for item in guest_cart.items.all():
        existing = user_cart.items.filter(product=item.product, variant=item.variant).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()
    guest_cart.delete()


# ── Storefront Views ────────────────────────────────────────────────────────

def home(request):
    featured_products = Product.objects.filter(
        is_active=True, is_featured=True
    ).select_related('brand', 'category').prefetch_related('images')[:8]

    sale_products = Product.objects.filter(
        is_active=True, sale_price__isnull=False
    ).select_related('brand', 'category').prefetch_related('images')[:8]

    top_categories = Category.objects.filter(
        is_active=True, parent=None
    ).order_by('order', 'name')[:8]

    new_arrivals = Product.objects.filter(
        is_active=True
    ).select_related('brand', 'category').prefetch_related('images').order_by('-created_at')[:8]

    context = {
        'featured_products': featured_products,
        'sale_products': sale_products,
        'top_categories': top_categories,
        'new_arrivals': new_arrivals,
    }
    return render(request, 'store/home.html', context)


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related(
        'brand', 'category'
    ).prefetch_related('images')

    # Filters
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    search_q = request.GET.get('q', '').strip()
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    on_sale = request.GET.get('on_sale')
    sort = request.GET.get('sort', '-created_at')

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        # Include subcategory products
        category_ids = [selected_category.pk] + list(
            selected_category.children.values_list('pk', flat=True)
        )
        products = products.filter(category_id__in=category_ids)

    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    if search_q:
        products = products.filter(
            Q(name__icontains=search_q) |
            Q(short_description__icontains=search_q) |
            Q(sku__icontains=search_q) |
            Q(tags__name__icontains=search_q)
        ).distinct()

    if min_price:
        try:
            products = products.filter(selling_price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            products = products.filter(selling_price__lte=float(max_price))
        except ValueError:
            pass

    if on_sale:
        products = products.filter(sale_price__isnull=False)

    SORT_OPTIONS = {
        'price_asc': 'selling_price',
        'price_desc': '-selling_price',
        'name_asc': 'name',
        'name_desc': '-name',
        '-created_at': '-created_at',
    }
    products = products.order_by(SORT_OPTIONS.get(sort, '-created_at'))

    paginator = Paginator(products, 12)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page,
        'products': page,
        'categories': Category.objects.filter(is_active=True, parent=None),
        'brands': Brand.objects.filter(is_active=True),
        'selected_category': selected_category,
        'selected_brand': brand_slug,
        'search_q': search_q,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'on_sale': on_sale,
        'sort': sort,
        'total_count': paginator.count,
    }
    return render(request, 'store/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand').prefetch_related(
            'images', 'variants', 'tags',
            'reviews__user',
        ),
        slug=slug, is_active=True,
    )

    reviews = product.reviews.filter(is_approved=True)
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    user_review = None
    review_form = None

    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        if not user_review:
            if request.method == 'POST' and 'submit_review' in request.POST:
                rating = request.POST.get('rating')
                title = request.POST.get('title', '')
                comment = request.POST.get('comment', '')
                if rating and comment:
                    ProductReview.objects.create(
                        product=product,
                        user=request.user,
                        rating=int(rating),
                        title=title,
                        comment=comment,
                    )
                    messages.success(request, 'Your review has been submitted and is pending approval.')
                    return redirect('store:product_detail', slug=slug)

    related = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(pk=product.pk).prefetch_related('images')[:4]

    # Check wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist = Wishlist.objects.filter(user=request.user).first()
        if wishlist:
            in_wishlist = wishlist.products.filter(pk=product.pk).exists()

    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'avg_rating_range': range(1, 6),
        'user_review': user_review,
        'related_products': related,
        'in_wishlist': in_wishlist,
    }
    return render(request, 'store/product_detail.html', context)


# ── Cart Views ──────────────────────────────────────────────────────────────

def cart_detail(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product', 'variant').prefetch_related('product__images')
    subtotal = cart.subtotal
    context = {
        'cart': cart,
        'items': items,
        'remaining_for_free_delivery': max(0, 2000 - subtotal),
    }
    return render(request, 'store/cart.html', context)


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    variant_id = request.POST.get('variant_id')
    variant = None
    if variant_id:
        from apps.products.models import ProductVariant
        variant = get_object_or_404(ProductVariant, pk=variant_id, product=product)

    item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, variant=variant,
        defaults={'quantity': quantity},
    )
    if not created:
        item.quantity += quantity
        item.save()

    messages.success(request, f'"{product.name}" added to cart.')
    next_url = request.POST.get('next', 'store:cart')
    if next_url == 'store:cart':
        return redirect('store:cart')
    return redirect(next_url)


@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    cart = get_or_create_cart(request)
    if item.cart != cart:
        messages.error(request, 'Invalid request.')
        return redirect('store:cart')
    quantity = int(request.POST.get('quantity', 1))
    if quantity < 1:
        item.delete()
        messages.success(request, 'Item removed from cart.')
    else:
        item.quantity = quantity
        item.save()
    return redirect('store:cart')


@require_POST
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id)
    cart = get_or_create_cart(request)
    if item.cart == cart:
        item.delete()
        messages.success(request, 'Item removed from cart.')
    return redirect('store:cart')


# ── Wishlist Views ──────────────────────────────────────────────────────────

@login_required
def wishlist_detail(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.filter(is_active=True).prefetch_related('images')
    return render(request, 'store/wishlist.html', {'wishlist': wishlist, 'products': products})


@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    if wishlist.products.filter(pk=product.pk).exists():
        wishlist.products.remove(product)
        added = False
        messages.info(request, f'"{product.name}" removed from wishlist.')
    else:
        wishlist.products.add(product)
        added = True
        messages.success(request, f'"{product.name}" added to wishlist.')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'count': wishlist.count})
    return redirect(request.POST.get('next', 'store:wishlist'))


# ── Checkout ────────────────────────────────────────────────────────────────

@login_required
def checkout(request):
    return redirect('orders:checkout')
