def cart_wishlist(request):
    """Inject cart item count and wishlist count into every template."""
    cart_count = 0
    wishlist_count = 0

    if request.user.is_authenticated:
        try:
            cart_count = request.user.cart.total_items
        except Exception:
            pass
        try:
            wishlist_count = request.user.wishlist.count
        except Exception:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            from apps.store.models import Cart
            cart = Cart.objects.filter(session_key=session_key).first()
            if cart:
                cart_count = cart.total_items

    return {'cart_count': cart_count, 'wishlist_count': wishlist_count}
