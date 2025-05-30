# PriceTracker/catalog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, PriceHistory, Tag, Store
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from .forms import PriceHistoryForm

def item_list(request):
    current_search_query = request.GET.get('q', '') 
    selected_tag_names = [tag.strip() for tag in request.GET.get('tags', '').split(',') if tag.strip()]

    items = Item.objects.all()

    if current_search_query:
        items = items.filter(name__icontains=current_search_query)
    
    if selected_tag_names:
        for tag_name in selected_tag_names:
            items = items.filter(tags__name__iexact=tag_name)

    items = items.distinct().order_by('name')

    price_form = PriceHistoryForm()
    all_tags = Tag.objects.all().order_by('name')

    context = {
        'items': items,
        'page_title': 'All Items',
        'search_query': current_search_query,
        'selected_tags': selected_tag_names,
        'all_tags': all_tags,
        'price_form': price_form,
    }
    return render(request, 'catalog/item_list.html', context)

def item_detail(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    price_entries = item.price_entries.all().order_by('-date_recorded')
    tags = item.tags.all()
    context = {
        'item': item,
        'price_entries': price_entries,
        'tags': tags,
        'page_title': item.name,
    }
    return render(request, 'catalog/item_detail.html', context)

def ajax_search_items(request):
    current_search_query = request.GET.get('q', '')
    selected_tag_names = [tag.strip() for tag in request.GET.get('tags', '').split(',') if tag.strip()]

    items = Item.objects.all()

    if current_search_query:
        items = items.filter(name__icontains=current_search_query)
    
    if selected_tag_names:
        for tag_name in selected_tag_names:
            items = items.filter(tags__name__iexact=tag_name)
            
    items = items.distinct().order_by('name')
    
    context = {
        'items': items, 
        'search_query': current_search_query,
        'selected_tags': selected_tag_names 
    }
    html_fragment = render_to_string('catalog/_item_list_fragment.html', context, request=request)
    return HttpResponse(html_fragment)


def ajax_get_last_purchase_details(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    last_purchase = item.price_entries.order_by('-date_recorded').first()
    
    data_to_return = {'store_id': None, 'product_url': None}

    if last_purchase:
        if last_purchase.store:
            data_to_return['store_id'] = last_purchase.store.id
        if last_purchase.product_url:
            data_to_return['product_url'] = last_purchase.product_url
            
    return JsonResponse(data_to_return)

def add_price_entry(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        form = PriceHistoryForm(request.POST, item_instance=item)
        if form.is_valid():
            price_entry = form.save(commit=False)
            price_entry.item = item
            price_entry.save()
            messages.success(request, f"Successfully added new price for '{item.name}'.")

            return redirect('catalog:item_detail', item_id=item.id)
        else:
            error_message = "Failed to add price. "
            for field, errors in form.errors.items():
                error_message += f"{field.replace('_', ' ').capitalize()}: {', '.join(errors)} "
            messages.error(request, error_message.strip())

            return redirect('catalog:item_list')

    return redirect('catalog:item_list')