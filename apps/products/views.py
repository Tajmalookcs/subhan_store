from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.forms import inlineformset_factory
from django.shortcuts import redirect
from django.db.models import Q

from apps.accounts.permissions import ManagerRequiredMixin, AdminRequiredMixin
from .models import Category, Brand, Product, ProductImage, ProductVariant
from .forms import CategoryForm, BrandForm, ProductForm, ProductImageForm, ProductVariantForm


# ── Formset factories ────────────────────────────────────────────────────────

ProductImageFormSet = inlineformset_factory(
    Product, ProductImage,
    form=ProductImageForm,
    extra=3, can_delete=True, max_num=10,
)

ProductVariantFormSet = inlineformset_factory(
    Product, ProductVariant,
    form=ProductVariantForm,
    extra=2, can_delete=True, max_num=20,
)


# ── Category Views ────────────────────────────────────────────────────────────

class CategoryListView(ManagerRequiredMixin, ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.select_related('parent').order_by('order', 'name')


class CategoryCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')
    success_message = 'Category "%(name)s" created successfully.'


class CategoryUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')
    success_message = 'Category "%(name)s" updated successfully.'


class CategoryDeleteView(AdminRequiredMixin, DeleteView):
    model = Category
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('products:category_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'Category'
        ctx['cancel_url'] = reverse_lazy('products:category_list')
        return ctx

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Category deleted successfully.')
        return super().post(request, *args, **kwargs)


# ── Brand Views ───────────────────────────────────────────────────────────────

class BrandListView(ManagerRequiredMixin, ListView):
    model = Brand
    template_name = 'products/brand_list.html'
    context_object_name = 'brands'
    queryset = Brand.objects.order_by('name')


class BrandCreateView(ManagerRequiredMixin, SuccessMessageMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'products/brand_form.html'
    success_url = reverse_lazy('products:brand_list')
    success_message = 'Brand "%(name)s" created successfully.'


class BrandUpdateView(ManagerRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'products/brand_form.html'
    success_url = reverse_lazy('products:brand_list')
    success_message = 'Brand "%(name)s" updated successfully.'


class BrandDeleteView(AdminRequiredMixin, DeleteView):
    model = Brand
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('products:brand_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'Brand'
        ctx['cancel_url'] = reverse_lazy('products:brand_list')
        return ctx

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Brand deleted successfully.')
        return super().post(request, *args, **kwargs)


# ── Product Views ─────────────────────────────────────────────────────────────

class ProductListView(ManagerRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'brand').order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        category = self.request.GET.get('category', '')
        status = self.request.GET.get('status', '')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))
        if category:
            qs = qs.filter(category_id=category)
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = Category.objects.filter(is_active=True).order_by('name')
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_category'] = self.request.GET.get('category', '')
        ctx['selected_status'] = self.request.GET.get('status', '')
        ctx['total_count'] = Product.objects.count()
        ctx['active_count'] = Product.objects.filter(is_active=True).count()
        ctx['low_stock_count'] = Product.objects.filter(
            stock_quantity__lte=10, is_active=True
        ).count()
        return ctx


class ProductDetailView(ManagerRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.prefetch_related(
            'images', 'variants', 'reviews__user', 'tags'
        ).select_related('category', 'brand')


class ProductCreateView(ManagerRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'image_formset' not in ctx:
            if self.request.POST:
                ctx['image_formset'] = ProductImageFormSet(self.request.POST, self.request.FILES)
                ctx['variant_formset'] = ProductVariantFormSet(self.request.POST)
            else:
                ctx['image_formset'] = ProductImageFormSet()
                ctx['variant_formset'] = ProductVariantFormSet()
        return ctx

    def form_valid(self, form):
        image_formset = ProductImageFormSet(self.request.POST, self.request.FILES)
        variant_formset = ProductVariantFormSet(self.request.POST)
        if image_formset.is_valid() and variant_formset.is_valid():
            form.instance.created_by = self.request.user
            self.object = form.save()
            image_formset.instance = self.object
            image_formset.save()
            variant_formset.instance = self.object
            variant_formset.save()
            messages.success(self.request, f'Product "{self.object.name}" created successfully.')
            return redirect('products:product_list')
        return self.render_to_response(self.get_context_data(
            form=form,
            image_formset=image_formset,
            variant_formset=variant_formset,
        ))


class ProductUpdateView(ManagerRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if 'image_formset' not in ctx:
            if self.request.POST:
                ctx['image_formset'] = ProductImageFormSet(
                    self.request.POST, self.request.FILES, instance=self.object
                )
                ctx['variant_formset'] = ProductVariantFormSet(
                    self.request.POST, instance=self.object
                )
            else:
                ctx['image_formset'] = ProductImageFormSet(instance=self.object)
                ctx['variant_formset'] = ProductVariantFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        image_formset = ProductImageFormSet(
            self.request.POST, self.request.FILES, instance=self.object
        )
        variant_formset = ProductVariantFormSet(self.request.POST, instance=self.object)
        if image_formset.is_valid() and variant_formset.is_valid():
            self.object = form.save()
            image_formset.instance = self.object
            image_formset.save()
            variant_formset.instance = self.object
            variant_formset.save()
            messages.success(self.request, f'Product "{self.object.name}" updated successfully.')
            return redirect('products:product_list')
        return self.render_to_response(self.get_context_data(
            form=form,
            image_formset=image_formset,
            variant_formset=variant_formset,
        ))


class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'products/confirm_delete.html'
    success_url = reverse_lazy('products:product_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['object_type'] = 'Product'
        ctx['cancel_url'] = reverse_lazy('products:product_list')
        return ctx

    def post(self, request, *args, **kwargs):
        messages.success(request, 'Product deleted successfully.')
        return super().post(request, *args, **kwargs)
