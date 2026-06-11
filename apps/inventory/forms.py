from django import forms
from .models import StockMovement, ExpiryRecord, Warehouse
from apps.products.models import Product


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'warehouse', 'movement_type', 'quantity', 'reference', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PO / Invoice number'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, movement_type_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        if movement_type_choices:
            self.fields['movement_type'].choices = movement_type_choices
        # Pre-select default warehouse
        default = Warehouse.get_default()
        if default and not self.instance.pk:
            self.fields['warehouse'].initial = default.pk


class ExpiryRecordForm(forms.ModelForm):
    class Meta:
        model = ExpiryRecord
        fields = ['product', 'warehouse', 'batch_number', 'quantity', 'expiry_date', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'warehouse': forms.Select(attrs={'class': 'form-select'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional batch / lot number'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True).order_by('name')
        self.fields['warehouse'].queryset = Warehouse.objects.filter(is_active=True)
        default = Warehouse.get_default()
        if default and not self.instance.pk:
            self.fields['warehouse'].initial = default.pk
