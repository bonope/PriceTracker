# PriceTracker/catalog/models.py
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Store(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website_url = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class PriceHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='price_entries')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='price_entries')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='HUF')
    date_recorded = models.DateTimeField(default=timezone.now)
    on_sale = models.BooleanField(default=False, verbose_name="Is this a sale price?")
    pre_sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Original Price (before sale)")
    product_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Product URL (Optional)")

    class Meta:
        ordering = ['-date_recorded']
        verbose_name_plural = "Price Histories"

    def __str__(self):
        sale_info = " (Sale)" if self.on_sale else ""
        return f"{self.item.name} at {self.store.name} - {self.price} {self.currency}{sale_info} on {self.date_recorded.strftime('%Y-%m-%d')}"

class AttributeGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Name of the attribute group (e.g., Nutritional Information, Physical Dimensions)")
    description = models.TextField(blank=True, null=True, help_text="Optional description for the group.")
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which to display groups.")

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

class AttributeDefinition(models.Model):
    VALUE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean (Yes/No)'),
    ]

    group = models.ForeignKey(AttributeGroup, on_delete=models.CASCADE, related_name='attributes', help_text="The group this attribute belongs to.")
    name = models.CharField(max_length=100, help_text="Name of the attribute (e.g., Fat, Width, Processor Speed)")
    slug = models.SlugField(max_length=120, unique=True, blank=True, help_text="A unique slug for programmatic access. Auto-generated if blank.")
    unit = models.CharField(max_length=30, blank=True, null=True, help_text="Unit of measurement (e.g., g, cm, GHz). Leave blank if not applicable.")
    value_type = models.CharField(max_length=20, choices=VALUE_TYPE_CHOICES, default='text', help_text="The type of value this attribute holds.")
    description = models.TextField(blank=True, null=True, help_text="Optional description or help text for this attribute.")
    display_order = models.PositiveIntegerField(default=0, help_text="Order in which to display attributes within a group.")

    class Meta:
        ordering = ['group', 'display_order', 'name']
        unique_together = [['group', 'name']]

    def __str__(self):
        return f"{self.group.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.group.name}-{self.name}")

            original_slug = self.slug
            counter = 1
            while AttributeDefinition.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class ItemSpecification(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='specifications')
    attribute = models.ForeignKey(AttributeDefinition, on_delete=models.CASCADE, related_name='item_values')
    
    value_text = models.TextField(blank=True, null=True, help_text="Text representation of the value.")
    value_numeric = models.DecimalField(max_digits=15, decimal_places=5, blank=True, null=True, help_text="Numeric value, if applicable.")
    value_boolean = models.BooleanField(null=True, blank=True, help_text="Boolean value, if applicable. Null means not set.") 

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['attribute__group__display_order', 'attribute__display_order', 'attribute__name']
        unique_together = [['item', 'attribute']]
        verbose_name = "Item Specification"
        verbose_name_plural = "Item Specifications"

    def __str__(self):
        return f"{self.item.name} - {self.attribute.name}: {self.get_value_display()}"

    def get_value(self):
        """Returns the appropriate value based on the attribute's value_type."""
        if self.attribute.value_type == 'number' and self.value_numeric is not None:
            if self.value_numeric == self.value_numeric.to_integral_value():
                return self.value_numeric.to_integral_value()
            return self.value_numeric
        elif self.attribute.value_type == 'boolean' and self.value_boolean is not None:
            return self.value_boolean
        return self.value_text

    def get_value_display(self):
        """Returns a display-friendly version of the value."""
        val = self.get_value()

        if self.attribute.value_type == 'boolean':
            return "Yes" if val else ("No" if val is False else "N/A")
        
        if val is None:
            return "N/A"
            
        unit = f" {self.attribute.unit}" if self.attribute.unit else ""

        return f"{val}{unit}"

    def save(self, *args, **kwargs):
        if self.value_text is not None:
            if self.attribute.value_type == 'number':
                try:
                    self.value_numeric = float(self.value_text.strip())
                except (ValueError, TypeError):
                    pass 
            elif self.attribute.value_type == 'boolean':
                txt_lower = self.value_text.strip().lower()
                if txt_lower in ['true', 'yes', '1', 'on']:
                    self.value_boolean = True
                elif txt_lower in ['false', 'no', '0', 'off']:
                    self.value_boolean = False
                else:
                    self.value_boolean = None
        
        super().save(*args, **kwargs)