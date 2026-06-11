from django import forms
from .models import Category, Brand, Product, ProductImage, ProductVariant


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'parent', 'description', 'image', 'is_active', 'order')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        qs = Category.objects.filter(parent__isnull=True)
        if instance:
            qs = qs.exclude(pk=instance.pk)
        self.fields['parent'].queryset = qs
        self.fields['parent'].empty_label = '— Top Level —'
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.Textarea, forms.NumberInput)):
                field.widget.attrs.setdefault('class', 'form-control')
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ('name', 'logo', 'description', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.Textarea)):
                field.widget.attrs.setdefault('class', 'form-control')
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            'name', 'sku', 'barcode', 'category', 'brand', 'tags',
            'short_description', 'description',
            'cost_price', 'selling_price', 'sale_price', 'unit',
            'is_taxable', 'tax_rate',
            'stock_quantity', 'low_stock_threshold',
            'is_active', 'is_featured',
        )
        widgets = {
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('name')
        self.fields['brand'].empty_label = '— No Brand —'
        self.fields['brand'].queryset = Brand.objects.filter(is_active=True).order_by('name')
        skip = (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.Textarea)
        for name, field in self.fields.items():
            if not isinstance(field.widget, skip):
                field.widget.attrs.setdefault('class', 'form-control')
        self.fields['is_active'].widget.attrs['class'] = 'form-check-input'
        self.fields['is_featured'].widget.attrs['class'] = 'form-check-input'
        self.fields['is_taxable'].widget.attrs['class'] = 'form-check-input'


class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ('image', 'alt_text', 'is_primary', 'order')
        widgets = {
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ('name', 'value', 'sku_suffix', 'price_adjustment', 'stock_quantity', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Size'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Large'}),
            'sku_suffix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. -L'}),
            'price_adjustment': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
