"""
Authentication and account views for Subhan Super Store.
Covers login, logout, register, profile, password reset/change, and dashboards.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.contrib import messages
from django.views import View
from django.views.generic import UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import CustomUser
from .forms import (
    LoginForm,
    CustomerRegistrationForm,
    ProfileUpdateForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    CustomPasswordChangeForm,
    StaffCreationForm,
)
from .permissions import AdminRequiredMixin


# ── Authentication Views ────────────────────────────────────────────────────

class LoginView(View):
    """Handle user login with remember-me support."""

    template_name = 'accounts/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url())
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Handle remember me
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Session expires on browser close

            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next', user.get_dashboard_url())
            return redirect(next_url)

        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    """Handle user logout."""

    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('accounts:login')

    # Allow GET logout for convenience
    def get(self, request):
        logout(request)
        return redirect('accounts:login')


class RegisterView(View):
    """Handle customer registration."""

    template_name = 'accounts/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url())
        form = CustomerRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to Subhan Super Store.')
            return redirect('accounts:customer_dashboard')
        return render(request, self.template_name, {'form': form})


# ── Profile Views ───────────────────────────────────────────────────────────

class ProfileView(LoginRequiredMixin, View):
    """Display and update user profile."""

    template_name = 'accounts/profile.html'

    def get(self, request):
        form = ProfileUpdateForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)
        return render(request, self.template_name, {
            'form': form,
            'password_form': password_form,
        })

    def post(self, request):
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')

        return render(request, self.template_name, {
            'form': form,
            'password_form': password_form,
        })


class PasswordChangeView(LoginRequiredMixin, View):
    """Handle password change from profile page."""

    def post(self, request):
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
        return redirect('accounts:profile')


# ── Password Reset Views ────────────────────────────────────────────────────

class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'accounts/emails/password_reset_email.html'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


# ── Dashboard Views ─────────────────────────────────────────────────────────

class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    """Customer account portal."""

    template_name = 'accounts/customer_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        # Redirect staff members to the admin dashboard
        if request.user.is_authenticated and request.user.is_staff_member:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Account'
        return context


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    """Main ERP admin dashboard — accessible to all staff roles."""

    template_name = 'accounts/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_staff_member:
            return redirect('accounts:customer_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        import json
        from django.db.models import Sum, Count, Q
        from django.db.models.functions import TruncDate
        from django.utils import timezone
        from datetime import timedelta

        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=29)

        # ── User stats ──────────────────────────────────────────────────────
        context['total_customers'] = CustomUser.objects.filter(role='customer').count()
        context['total_staff'] = CustomUser.objects.exclude(role='customer').count()
        context['new_customers_today'] = CustomUser.objects.filter(
            role='customer', date_joined__date=today
        ).count()

        # ── Product / Inventory stats ────────────────────────────────────────
        try:
            from apps.products.models import Product, Category
            context['total_products'] = Product.objects.filter(is_active=True).count()
            from django.db.models import F as Fq
            context['low_stock_count'] = Product.objects.filter(
                is_active=True,
                stock_quantity__lte=Fq('low_stock_threshold'),
            ).count()
            context['out_of_stock_count'] = Product.objects.filter(
                is_active=True, stock_quantity__lte=0
            ).count()
            context['low_stock_products'] = Product.objects.filter(
                is_active=True,
                stock_quantity__lte=Fq('low_stock_threshold'),
            ).select_related('category').order_by('stock_quantity')[:8]
        except Exception:
            context['total_products'] = 0
            context['low_stock_count'] = 0
            context['out_of_stock_count'] = 0
            context['low_stock_products'] = []

        # ── Order stats ──────────────────────────────────────────────────────
        try:
            from apps.orders.models import Order
            orders_qs = Order.objects.exclude(status='cancelled')
            context['total_orders'] = orders_qs.count()
            context['pending_orders'] = Order.objects.filter(status='pending').count()
            context['orders_today'] = Order.objects.filter(created_at__date=today).count()
            context['online_revenue'] = orders_qs.aggregate(
                t=Sum('total_amount')
            )['t'] or 0
            context['recent_orders'] = Order.objects.select_related('user').order_by('-created_at')[:8]

            # Daily online revenue — last 30 days
            daily_online = dict(
                Order.objects.filter(
                    created_at__date__gte=thirty_days_ago
                ).exclude(status='cancelled').annotate(
                    day=TruncDate('created_at')
                ).values('day').annotate(rev=Sum('total_amount')).values_list('day', 'rev')
            )
        except Exception:
            context['total_orders'] = 0
            context['pending_orders'] = 0
            context['orders_today'] = 0
            context['online_revenue'] = 0
            context['recent_orders'] = []
            daily_online = {}

        # ── POS stats ────────────────────────────────────────────────────────
        try:
            from apps.pos.models import POSSale, POSSession
            pos_qs = POSSale.objects.filter(is_void=False)
            context['pos_revenue'] = pos_qs.aggregate(t=Sum('total_amount'))['t'] or 0
            context['pos_sales_today'] = pos_qs.filter(created_at__date=today).count()
            context['pos_revenue_today'] = pos_qs.filter(
                created_at__date=today
            ).aggregate(t=Sum('total_amount'))['t'] or 0
            context['open_sessions'] = POSSession.objects.filter(status='open').count()
            context['recent_pos_sales'] = pos_qs.select_related('cashier').order_by('-created_at')[:8]

            # Daily POS revenue
            daily_pos = dict(
                pos_qs.filter(
                    created_at__date__gte=thirty_days_ago
                ).annotate(day=TruncDate('created_at')).values('day').annotate(
                    rev=Sum('total_amount')
                ).values_list('day', 'rev')
            )

            # Payment method breakdown (POS)
            pm_data = list(
                pos_qs.values('payment_method').annotate(
                    total=Sum('total_amount'), cnt=Count('id')
                ).order_by('-total')
            )
            context['payment_labels'] = json.dumps([p['payment_method'].title() for p in pm_data])
            context['payment_values'] = json.dumps([float(p['total'] or 0) for p in pm_data])

            # Top products (POS)
            from apps.pos.models import POSSaleItem
            top_products = list(
                POSSaleItem.objects.values('product_name').annotate(
                    qty=Sum('quantity'), rev=Sum('line_total')
                ).order_by('-qty')[:7]
            )
            context['top_product_labels'] = json.dumps([p['product_name'][:20] for p in top_products])
            context['top_product_qty'] = json.dumps([int(p['qty']) for p in top_products])

        except Exception:
            context['pos_revenue'] = 0
            context['pos_sales_today'] = 0
            context['pos_revenue_today'] = 0
            context['open_sessions'] = 0
            context['recent_pos_sales'] = []
            daily_pos = {}
            context['payment_labels'] = json.dumps([])
            context['payment_values'] = json.dumps([])
            context['top_product_labels'] = json.dumps([])
            context['top_product_qty'] = json.dumps([])

        # ── Combined revenue ─────────────────────────────────────────────────
        context['total_revenue'] = float(context['online_revenue']) + float(context['pos_revenue'])
        context['today_revenue'] = float(context.get('pos_revenue_today', 0))

        # ── Daily combined chart (last 30 days) ──────────────────────────────
        date_labels, online_series, pos_series = [], [], []
        for i in range(30):
            day = thirty_days_ago + timedelta(days=i)
            date_labels.append(day.strftime('%d %b'))
            online_series.append(float(daily_online.get(day, 0)))
            pos_series.append(float(daily_pos.get(day, 0)))

        context['chart_labels'] = json.dumps(date_labels)
        context['chart_online'] = json.dumps(online_series)
        context['chart_pos'] = json.dumps(pos_series)

        return context




# ── Staff Management (Admin only) ───────────────────────────────────────────

class StaffListView(AdminRequiredMixin, TemplateView):
    """List all staff members."""

    template_name = 'accounts/staff_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['staff'] = CustomUser.objects.exclude(role='customer').order_by('role', 'username')
        context['title'] = 'Staff Management'
        return context


class StaffCreateView(AdminRequiredMixin, View):
    """Create a new staff user."""

    template_name = 'accounts/staff_create.html'

    def get(self, request):
        form = StaffCreationForm()
        return render(request, self.template_name, {'form': form, 'title': 'Add Staff Member'})

    def post(self, request):
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff member created successfully.')
            return redirect('accounts:staff_list')
        return render(request, self.template_name, {'form': form, 'title': 'Add Staff Member'})


class HomeRedirectView(View):
    """Redirect root URL based on authentication status."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url())
        return redirect('accounts:login')
