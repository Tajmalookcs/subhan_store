import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db import transaction

from apps.products.models import Product
from apps.inventory.models import StockMovement, Warehouse
from .models import POSSession, POSSale, POSSaleItem


def cashier_required(view_func):
    """Allow only cashier roles and above."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_cashier:
            messages.error(request, 'POS access requires cashier role or above.')
            return redirect('accounts:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_open_session(user):
    return POSSession.objects.filter(cashier=user, status='open').first()


# ── Session Management ──────────────────────────────────────────────────────

@cashier_required
def pos_redirect(request):
    session = get_open_session(request.user)
    if session:
        return redirect('pos:screen')
    return redirect('pos:session_open')


@cashier_required
def session_open(request):
    if get_open_session(request.user):
        return redirect('pos:screen')
    if request.method == 'POST':
        opening_cash = request.POST.get('opening_cash', '0')
        notes = request.POST.get('notes', '')
        try:
            opening_cash = Decimal(opening_cash)
        except Exception:
            opening_cash = Decimal('0')
        POSSession.objects.create(
            cashier=request.user,
            opening_cash=opening_cash,
            notes=notes,
        )
        messages.success(request, 'POS session opened. Ready to sell!')
        return redirect('pos:screen')
    return render(request, 'pos/session_open.html')


@cashier_required
def session_close(request):
    session = get_open_session(request.user)
    if not session:
        messages.warning(request, 'No open session found.')
        return redirect('pos:session_list')
    if request.method == 'POST':
        closing_cash = request.POST.get('closing_cash', '0')
        try:
            closing_cash = Decimal(closing_cash)
        except Exception:
            closing_cash = Decimal('0')
        session.closing_cash = closing_cash
        session.status = 'closed'
        session.closed_at = timezone.now()
        session.save()
        messages.success(request, f'Session closed. Total revenue: Rs. {session.total_revenue}')
        return redirect('pos:session_detail', pk=session.pk)
    sales = session.sales.filter(is_void=False).select_related()
    return render(request, 'pos/session_close.html', {'session': session, 'sales': sales})


@cashier_required
def session_list(request):
    if request.user.is_manager:
        sessions = POSSession.objects.select_related('cashier')
    else:
        sessions = POSSession.objects.filter(cashier=request.user)
    return render(request, 'pos/session_list.html', {'sessions': sessions})


@cashier_required
def session_detail(request, pk):
    if request.user.is_manager:
        session = get_object_or_404(POSSession, pk=pk)
    else:
        session = get_object_or_404(POSSession, pk=pk, cashier=request.user)
    sales = session.sales.filter(is_void=False).prefetch_related('items')
    return render(request, 'pos/session_detail.html', {'session': session, 'sales': sales})


# ── POS Screen ──────────────────────────────────────────────────────────────

@cashier_required
def pos_screen(request):
    session = get_open_session(request.user)
    if not session:
        messages.warning(request, 'Please open a session first.')
        return redirect('pos:session_open')
    recent_sales = session.sales.filter(is_void=False).order_by('-created_at')[:5]
    return render(request, 'pos/pos_screen.html', {
        'session': session,
        'recent_sales': recent_sales,
    })


# ── AJAX Endpoints ──────────────────────────────────────────────────────────

@login_required
def product_search(request):
    """JSON: search product by name or barcode."""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})

    from django.db.models import Q
    products = Product.objects.filter(
        Q(name__icontains=q) | Q(barcode__iexact=q) | Q(sku__iexact=q),
        is_active=True,
        stock_quantity__gt=0,
    ).select_related('category').prefetch_related('images')[:20]

    results = []
    for p in products:
        img = p.primary_image
        results.append({
            'id': p.pk,
            'name': p.name,
            'sku': p.sku,
            'barcode': p.barcode,
            'price': str(p.effective_price),
            'stock': p.stock_quantity,
            'unit': p.get_unit_display(),
            'category': p.category.name,
            'image': img.image.url if img else '',
        })
    return JsonResponse({'results': results})


@login_required
@require_POST
def process_sale(request):
    """JSON: process a completed POS sale."""
    session = get_open_session(request.user)
    if not session:
        return JsonResponse({'error': 'No open session.'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid data.'}, status=400)

    items_data = data.get('items', [])
    if not items_data:
        return JsonResponse({'error': 'Cart is empty.'}, status=400)

    payment_method = data.get('payment_method', 'cash')
    amount_tendered = Decimal(str(data.get('amount_tendered', '0')))
    discount_amount = Decimal(str(data.get('discount_amount', '0')))
    customer_name = data.get('customer_name', '')
    notes = data.get('notes', '')

    warehouse = Warehouse.get_default()

    with transaction.atomic():
        subtotal = Decimal('0')
        validated_items = []

        for item in items_data:
            product = get_object_or_404(Product, pk=item['product_id'], is_active=True)
            qty = int(item['quantity'])
            if qty < 1:
                continue
            if product.stock_quantity < qty:
                return JsonResponse(
                    {'error': f'Insufficient stock for {product.name}. Available: {product.stock_quantity}'},
                    status=400,
                )
            unit_price = product.effective_price
            disc_pct = Decimal(str(item.get('discount_percent', '0')))
            discounted_price = unit_price * (1 - disc_pct / 100)
            line_total = discounted_price * qty
            subtotal += line_total
            validated_items.append({
                'product': product,
                'product_name': product.name,
                'unit_price': unit_price,
                'quantity': qty,
                'discount_percent': disc_pct,
                'line_total': line_total,
            })

        total_amount = subtotal - discount_amount
        if total_amount < 0:
            total_amount = Decimal('0')
        change_amount = max(amount_tendered - total_amount, Decimal('0'))

        sale = POSSale.objects.create(
            session=session,
            cashier=request.user,
            subtotal=subtotal,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            amount_tendered=amount_tendered,
            change_amount=change_amount,
            customer_name=customer_name,
            notes=notes,
        )

        for vi in validated_items:
            POSSaleItem.objects.create(
                sale=sale,
                product=vi['product'],
                product_name=vi['product_name'],
                unit_price=vi['unit_price'],
                quantity=vi['quantity'],
                discount_percent=vi['discount_percent'],
                line_total=vi['line_total'],
            )
            # Decrement stock via StockMovement
            if warehouse:
                StockMovement.objects.create(
                    product=vi['product'],
                    warehouse=warehouse,
                    movement_type='sale',
                    quantity=vi['quantity'],
                    reference=sale.sale_number,
                    created_by=request.user,
                )

    return JsonResponse({
        'success': True,
        'sale_number': sale.sale_number,
        'total_amount': str(sale.total_amount),
        'change_amount': str(sale.change_amount),
        'receipt_url': f'/pos/receipt/{sale.sale_number}/',
    })


# ── Receipt & Void ──────────────────────────────────────────────────────────

@cashier_required
def receipt(request, sale_number):
    sale = get_object_or_404(POSSale, sale_number=sale_number)
    if not request.user.is_manager and sale.cashier != request.user:
        messages.error(request, 'Access denied.')
        return redirect('pos:screen')
    items = sale.items.select_related('product')
    return render(request, 'pos/receipt.html', {'sale': sale, 'items': items})


@cashier_required
@require_POST
def sale_void(request, sale_number):
    if not request.user.is_manager:
        messages.error(request, 'Only managers can void sales.')
        return redirect('pos:receipt', sale_number=sale_number)
    sale = get_object_or_404(POSSale, sale_number=sale_number, is_void=False)
    warehouse = Warehouse.get_default()
    with transaction.atomic():
        # Restore stock
        for item in sale.items.all():
            if warehouse:
                StockMovement.objects.create(
                    product=item.product,
                    warehouse=warehouse,
                    movement_type='adjustment_in',
                    quantity=item.quantity,
                    reference=f'VOID-{sale.sale_number}',
                    created_by=request.user,
                )
        sale.is_void = True
        sale.voided_by = request.user
        sale.voided_at = timezone.now()
        sale.save()
    messages.success(request, f'Sale {sale_number} has been voided and stock restored.')
    return redirect('pos:session_detail', pk=sale.session_id)
