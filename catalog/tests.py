# catalog/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from .models import Item, Store, PriceHistory, Tag
from .forms import PriceHistoryForm


class ItemModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(
            name="Test Product",
            description="A test product description"
        )
        self.tag = Tag.objects.create(name="Electronics")
        self.item.tags.add(self.tag)
    
    def test_string_representation(self):
        self.assertEqual(str(self.item), "Test Product")
    
    def test_item_creation(self):
        self.assertTrue(isinstance(self.item, Item))
        self.assertEqual(self.item.name, "Test Product")
        self.assertEqual(self.item.tags.count(), 1)


class StoreModelTest(TestCase):
    def test_store_creation(self):
        store = Store.objects.create(
            name="Test Store",
            website_url="https://example.com"
        )
        self.assertEqual(str(store), "Test Store")


class PriceHistoryModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Test Item")
        self.store = Store.objects.create(name="Test Store")
        
    def test_price_history_creation(self):
        price_entry = PriceHistory.objects.create(
            item=self.item,
            store=self.store,
            price=Decimal('99.99'),
            currency='HUF'
        )
        self.assertTrue(isinstance(price_entry, PriceHistory))
        self.assertEqual(price_entry.price, Decimal('99.99'))
        
    def test_sale_price_validation(self):
        price_entry = PriceHistory.objects.create(
            item=self.item,
            store=self.store,
            price=Decimal('79.99'),
            on_sale=True,
            pre_sale_price=Decimal('99.99')
        )
        self.assertTrue(price_entry.on_sale)
        self.assertEqual(price_entry.pre_sale_price, Decimal('99.99'))


class ItemListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.item1 = Item.objects.create(name="Apple iPhone 15")
        self.item2 = Item.objects.create(name="Samsung Galaxy S24")
        self.tag = Tag.objects.create(name="Smartphones")
        self.item1.tags.add(self.tag)
        self.item2.tags.add(self.tag)
        
    def test_item_list_view(self):
        response = self.client.get(reverse('catalog:item_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apple iPhone 15")
        self.assertContains(response, "Samsung Galaxy S24")
        
    def test_search_functionality(self):
        response = self.client.get(reverse('catalog:item_list'), {'q': 'iPhone'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apple iPhone 15")
        self.assertNotContains(response, "Samsung Galaxy S24")
        
    def test_tag_filtering(self):
        response = self.client.get(reverse('catalog:item_list'), {'tags': 'Smartphones'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Apple iPhone 15")
        self.assertContains(response, "Samsung Galaxy S24")
        
    def test_ajax_search(self):
        response = self.client.get(
            reverse('catalog:ajax_search_items'),
            {'q': 'Galaxy'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Samsung Galaxy S24")
        self.assertNotContains(response, "Apple iPhone 15")


class ItemDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.item = Item.objects.create(
            name="Test Product",
            description="Detailed description"
        )
        self.store = Store.objects.create(name="Amazon")
        self.price_entry = PriceHistory.objects.create(
            item=self.item,
            store=self.store,
            price=Decimal('149.99')
        )
        
    def test_item_detail_view(self):
        response = self.client.get(
            reverse('catalog:item_detail', kwargs={'item_id': self.item.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")
        self.assertContains(response, "Detailed description")
        self.assertContains(response, "149.99")
        self.assertContains(response, "Amazon")


class PriceHistoryFormTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(name="Test Store")
        
    def test_valid_form(self):
        form_data = {
            'store': self.store.id,
            'price': '99.99',
            'date_recorded': timezone.now().date(),
            'on_sale': False,
            'currency': 'HUF'
        }
        form = PriceHistoryForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_sale_price_validation(self):
        # Test that sale price must have pre_sale_price
        form_data = {
            'store': self.store.id,
            'price': '79.99',
            'date_recorded': timezone.now().date(),
            'on_sale': True,
            # Missing pre_sale_price
        }
        form = PriceHistoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pre_sale_price', form.errors)
        
    def test_pre_sale_price_must_be_higher(self):
        form_data = {
            'store': self.store.id,
            'price': '99.99',
            'date_recorded': timezone.now().date(),
            'on_sale': True,
            'pre_sale_price': '79.99'  # Lower than sale price
        }
        form = PriceHistoryForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('pre_sale_price', form.errors)


class AddPriceEntryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.item = Item.objects.create(name="Test Item")
        self.store = Store.objects.create(name="Test Store")
        
    def test_add_price_entry(self):
        form_data = {
            'store': self.store.id,
            'price': '99.99',
            'date_recorded': timezone.now().date(),
            'on_sale': False,
        }
        response = self.client.post(
            reverse('catalog:add_price_entry', kwargs={'item_id': self.item.id}),
            data=form_data
        )
        # Should redirect to item detail page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, 
            reverse('catalog:item_detail', kwargs={'item_id': self.item.id})
        )
        
        # Check that price was actually added
        self.assertEqual(self.item.price_entries.count(), 1)
        price_entry = self.item.price_entries.first()
        self.assertEqual(price_entry.price, Decimal('99.99'))
        
    def test_ajax_last_purchase_details(self):
        # Create a previous purchase
        PriceHistory.objects.create(
            item=self.item,
            store=self.store,
            price=Decimal('89.99'),
            product_url='https://example.com/product'
        )
        
        response = self.client.get(
            reverse('catalog:ajax_get_last_purchase_details', 
                    kwargs={'item_id': self.item.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['store_id'], self.store.id)
        self.assertEqual(data['product_url'], 'https://example.com/product')