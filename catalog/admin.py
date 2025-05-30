# PriceTracker/catalog/admin.py
from django.contrib import admin
from .models import Tag, Store, Item, PriceHistory, AttributeGroup, AttributeDefinition, ItemSpecification

admin.site.register(Tag)
admin.site.register(Store)

@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'display_order')
    search_fields = ('name', 'description')

@admin.register(AttributeDefinition)
class AttributeDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'value_type', 'unit', 'slug', 'display_order')
    list_filter = ('group', 'value_type')
    search_fields = ('name', 'slug', 'group__name')
    prepopulated_fields = {'slug': ('name',)}

class ItemSpecificationInline(admin.TabularInline):
    model = ItemSpecification
    extra = 1
    
    fields = ('attribute', 'value_text', 'value_numeric', 'value_boolean')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "attribute":
            kwargs["queryset"] = AttributeDefinition.objects.order_by('group__name', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_tags_display', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('tags',)
    inlines = [ItemSpecificationInline]

    def get_tags_display(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    get_tags_display.short_description = 'Tags'

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('item', 'store', 'price', 'currency', 'date_recorded', 'on_sale', 'pre_sale_price', 'product_url')
    list_filter = ('item__name', 'store__name', 'on_sale', 'date_recorded')
    search_fields = ('item__name', 'store__name', 'product_url')