from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.store.views import get_or_create_cart
from .models import Order, OrderItem, OrderStatusHistory
from .forms import CheckoutForm, OrderStatusForm
from apps.accounts.permissions import ManagerRequiredMixin
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin


FREE_DELIVERY_THRESHOLD = Decimal('2000')
DELIVERY_CHARGE = Decimal('150')


# ── Customer Views ──────────────────────────────────────────────────────────

@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    items = cart.items.select_related('product', 'variant').prefetch_related('product__images')

    if not items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:cart')

    subtotal = cart.subtotal
    delivery = Decimal('0') if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_CHARGE
    total = subtotal + delivery

    initial = {
        'shipping_name': request.user.get_full_name() or request.user.username,
        'shipping_phone': request.user.phone,
        'shipping_email': request.user.email,
        'shipping_address': request.user.address,
        'shipping_city': 'Jaranwala',
    }

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            order = Order.objects.create(
                user=request.user,
                shipping_name=d['shipping_name'],
                shipping_phone=d['shipping_phone'],
                shipping_email=d['shipping_email'],
                shipping_address=d['shipping_address'],
                shipping_city=d['shipping_city'],
                shipping_postal_code=d.get('shipping_postal_code', ''),
                payment_method=d['payment_method'],
                notes=d.get('notes', ''),
                subtotal=subtotal,
                delivery_charge=delivery,
                total_amount=total,
            )

            for item in items:
                variant_info = ''
                if item.variant:
                    variant_info = f'{item.variant.name}: {item.variant.value}'
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    product_name=item.product.name,
                    variant_info=variant_info,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                )

            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                note='Order placed by customer.',
                changed_by=request.user,
            )

            # Clear cart
            cart.items.all().delete()

            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('orders:order_detail', order_number=order.order_number)
    else:
        form = CheckoutForm(initial=initial)

    context = {
        'form': form,
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'delivery': delivery,
        'total': total,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    items = order.items.select_related('product')
    history = order.history.all()
    return render(request, 'orders/order_detail.html', {
        'order': order, 'items': items, 'history': history,
    })


@login_required
def order_cancel(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if not order.can_cancel():
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_detail', order_number=order_number)
    if request.method == 'POST':
        order.status = 'cancelled'
        order.save()
        OrderStatusHistory.objects.create(
            order=order, status='cancelled',
            note='Cancelled by customer.', changed_by=request.user,
        )
        messages.success(request, f'Order {order.order_number} has been cancelled.')
        return redirect('orders:order_list')
    return render(request, 'orders/order_cancel_confirm.html', {'order': order})


@login_required
def invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    items = order.items.select_related('product')
    return render(request, 'orders/invoice.html', {'order': order, 'items': items})


# ── Admin/Staff Order Management ────────────────────────────────────────────

@login_required
def admin_order_list(request):
    if not request.user.is_manager:
        messages.error(request, 'Access denied.')
        return redirect('store:home')

    orders = Order.objects.select_related('user').prefetch_related('items')

    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment', '')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'orders/admin/order_list.html', context)


@login_required
def admin_order_detail(request, order_number):
    if not request.user.is_manager:
        messages.error(request, 'Access denied.')
        return redirect('store:home')

    order = get_object_or_404(Order, order_number=order_number)
    items = order.items.select_related('product')
    history = order.history.select_related('changed_by')
    form = OrderStatusForm(instance=order)

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            old_status = order.status
            note = request.POST.get('note', '')
            updated = form.save()
            if updated.status != old_status:
                OrderStatusHistory.objects.create(
                    order=updated, status=updated.status,
                    note=note, changed_by=request.user,
                )
                if updated.status == 'confirmed':
                    updated.confirmed_at = timezone.now()
                    updated.save(update_fields=['confirmed_at'])
                elif updated.status == 'delivered':
                    updated.delivered_at = timezone.now()
                    updated.payment_status = 'paid' if updated.payment_method == 'cod' else updated.payment_status
                    updated.save(update_fields=['delivered_at', 'payment_status'])
            messages.success(request, 'Order updated.')
            return redirect('orders:admin_order_detail', order_number=order_number)

    context = {
        'order': order, 'items': items, 'history': history, 'form': form,
    }
    return render(request, 'orders/admin/order_detail.html', context)
