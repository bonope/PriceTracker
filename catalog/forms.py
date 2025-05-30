# PriceTracker/catalog/forms.py
from django import forms
from .models import Store, PriceHistory, Item
from django.utils import timezone

class PriceHistoryForm(forms.ModelForm):
    date_recorded = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        initial=timezone.now().date,
        label="Date"
    )
    store = forms.ModelChoiceField(
        queryset=Store.objects.all().order_by('name'),
        empty_label="-- Select a Store --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        label="Price Paid / Sale Price"
    )
    on_sale = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Is this a sale price?"
    )
    pre_sale_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        label="Original Price (if on sale)",
    )
    product_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/product-page'}),
        label="Product URL"
    )

    class Meta:
        model = PriceHistory
        fields = ['store', 'price', 'date_recorded', 'on_sale', 'pre_sale_price', 'product_url'] 

    def __init__(self, *args, **kwargs):
        self.item_instance = kwargs.pop('item_instance', None)
        super().__init__(*args, **kwargs)

        if self.item_instance:
            last_purchase = PriceHistory.objects.filter(item=self.item_instance).order_by('-date_recorded').first()
            if last_purchase and last_purchase.store:
                self.fields['store'].initial = last_purchase.store
            if last_purchase.product_url and self.fields['store'].initial == last_purchase.store:
                self.fields['product_url'].initial = last_purchase.product_url        

    def clean(self):
        cleaned_data = super().clean()
        on_sale = cleaned_data.get("on_sale")
        pre_sale_price = cleaned_data.get("pre_sale_price")
        price = cleaned_data.get("price")

        if on_sale:
            if pre_sale_price is None:
                self.add_error('pre_sale_price', "Original price is required when 'Is this a sale price?' is checked.")
            elif price is not None and pre_sale_price <= price:
                self.add_error('pre_sale_price', "Original price must be greater than the sale price.")
        elif not on_sale and pre_sale_price is not None:
            cleaned_data['pre_sale_price'] = None

        return cleaned_data