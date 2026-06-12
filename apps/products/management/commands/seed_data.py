"""
Management command to populate the database with sample store data.
Usage: python manage.py seed_data
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with sample products, categories, and brands'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')
        self._create_categories()
        self._create_brands()
        self._create_products()
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

    # ── Categories ──────────────────────────────────────────────────────────

    def _create_categories(self):
        from apps.products.models import Category

        top_level = [
            ('Grocery & Staples', 0),
            ('Beverages', 1),
            ('Dairy & Eggs', 2),
            ('Bakery & Snacks', 3),
            ('Personal Care', 4),
            ('Household', 5),
            ('Frozen Foods', 6),
            ('Fruits & Vegetables', 7),
        ]
        self.categories = {}
        for name, order in top_level:
            cat, _ = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'order': order, 'is_active': True},
            )
            self.categories[name] = cat

        sub = [
            ('Rice & Grains', 'Grocery & Staples'),
            ('Cooking Oil', 'Grocery & Staples'),
            ('Spices & Masala', 'Grocery & Staples'),
            ('Pulses & Lentils', 'Grocery & Staples'),
            ('Cold Drinks', 'Beverages'),
            ('Juices', 'Beverages'),
            ('Tea & Coffee', 'Beverages'),
            ('Water', 'Beverages'),
            ('Milk', 'Dairy & Eggs'),
            ('Yogurt & Cream', 'Dairy & Eggs'),
            ('Butter & Cheese', 'Dairy & Eggs'),
            ('Bread & Roti', 'Bakery & Snacks'),
            ('Biscuits & Cookies', 'Bakery & Snacks'),
            ('Chips & Crisps', 'Bakery & Snacks'),
            ('Shampoo & Hair Care', 'Personal Care'),
            ('Soap & Body Wash', 'Personal Care'),
            ('Oral Care', 'Personal Care'),
            ('Detergents', 'Household'),
            ('Dishwash', 'Household'),
            ('Tissues & Paper', 'Household'),
        ]
        for name, parent_name in sub:
            parent = self.categories[parent_name]
            cat, _ = Category.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'parent': parent, 'is_active': True},
            )
            self.categories[name] = cat

        self.stdout.write(f'  Categories: {len(self.categories)}')

    # ── Brands ───────────────────────────────────────────────────────────────

    def _create_brands(self):
        from apps.products.models import Brand

        names = [
            'Nestle', 'Unilever', 'National Foods', 'Shan Foods',
            'Olpers', 'Shezan', 'Pepsi', 'Coca-Cola', 'Gourmet',
            'Dawn Bread', 'Tapal', 'Lipton', 'Sunsilk', 'Head & Shoulders',
            'Colgate', 'Surf Excel', 'Vim', 'Lays', 'Pringles', 'Dalda',
        ]
        self.brands = {}
        for name in names:
            brand, _ = Brand.objects.get_or_create(
                slug=slugify(name),
                defaults={'name': name, 'is_active': True},
            )
            self.brands[name] = brand

        self.stdout.write(f'  Brands: {len(self.brands)}')

    # ── Products ─────────────────────────────────────────────────────────────

    def _create_products(self):
        from apps.products.models import Product

        products = self._product_data()
        created = 0
        for data in products:
            _, made = Product.objects.get_or_create(
                sku=data['sku'],
                defaults=data,
            )
            if made:
                created += 1

        self.stdout.write(f'  Products: {Product.objects.count()} total ({created} new)')

    def _product_data(self):
        c = self.categories
        b = self.brands

        def p(sku, name, cat, brand, cost, price, sale=None, stock=100,
              featured=False, unit='pcs', desc=''):
            d = {
                'sku': sku,
                'name': name,
                'category': c[cat],
                'brand': b[brand],
                'cost_price': Decimal(str(cost)),
                'selling_price': Decimal(str(price)),
                'stock_quantity': stock,
                'is_featured': featured,
                'is_active': True,
                'unit': unit,
                'short_description': desc or name,
                'low_stock_threshold': 10,
            }
            if sale:
                d['sale_price'] = Decimal(str(sale))
            return d

        return [
            # ── Rice & Grains
            p('GRC-001', 'Basmati Rice 5kg', 'Rice & Grains', 'National Foods',
              700, 950, stock=200, featured=True, unit='pack',
              desc='Premium long-grain basmati rice, aged for best aroma'),
            p('GRC-002', 'Basmati Rice 1kg', 'Rice & Grains', 'National Foods',
              160, 220, stock=300, unit='pack'),
            p('GRC-003', 'Super Kernel Rice 5kg', 'Rice & Grains', 'Gourmet',
              650, 890, sale=820, stock=150, unit='pack',
              desc='Extra-long grain, fluffy texture perfect for biryani'),
            p('GRC-004', 'Wheat Flour Atta 10kg', 'Rice & Grains', 'Gourmet',
              900, 1200, stock=180, unit='pack',
              desc='Fine-milled whole wheat flour for soft rotis'),

            # ── Cooking Oil
            p('OIL-001', 'Dalda Cooking Oil 5 Litre', 'Cooking Oil', 'Dalda',
              1100, 1450, sale=1350, stock=120, featured=True, unit='ltr',
              desc='Refined vegetable oil, cholesterol-free'),
            p('OIL-002', 'Dalda Cooking Oil 1 Litre', 'Cooking Oil', 'Dalda',
              280, 360, stock=250, unit='ltr'),
            p('OIL-003', 'Sunflower Oil 3 Litre', 'Cooking Oil', 'National Foods',
              750, 980, sale=920, stock=100, unit='ltr',
              desc='Light sunflower oil ideal for frying'),

            # ── Spices
            p('SPC-001', 'Shan Biryani Masala 60g', 'Spices & Masala', 'Shan Foods',
              55, 85, stock=400, featured=True, unit='pack',
              desc='Authentic spice blend for restaurant-style biryani'),
            p('SPC-002', 'Shan Karahi Masala 100g', 'Spices & Masala', 'Shan Foods',
              65, 95, stock=350, unit='pack'),
            p('SPC-003', 'National Garam Masala 50g', 'Spices & Masala', 'National Foods',
              45, 70, stock=300, unit='pack'),
            p('SPC-004', 'National Chilli Powder 200g', 'Spices & Masala', 'National Foods',
              85, 120, sale=105, stock=280, unit='pack'),
            p('SPC-005', 'Shan Chicken Tikka 50g', 'Spices & Masala', 'Shan Foods',
              50, 80, stock=320, unit='pack'),

            # ── Pulses
            p('PLS-001', 'Moong Daal 1kg', 'Pulses & Lentils', 'National Foods',
              180, 240, stock=200, unit='kg'),
            p('PLS-002', 'Masoor Daal 1kg', 'Pulses & Lentils', 'National Foods',
              160, 210, stock=220, unit='kg'),
            p('PLS-003', 'Chana Daal 1kg', 'Pulses & Lentils', 'National Foods',
              140, 190, stock=210, unit='kg'),

            # ── Cold Drinks
            p('BVR-001', 'Pepsi 1.5 Litre', 'Cold Drinks', 'Pepsi',
              90, 130, stock=300, featured=True, unit='ltr',
              desc='Refreshing cola drink, chilled'),
            p('BVR-002', 'Pepsi 345ml Can', 'Cold Drinks', 'Pepsi',
              50, 75, stock=500, unit='ml'),
            p('BVR-003', 'Coca-Cola 1.5 Litre', 'Cold Drinks', 'Coca-Cola',
              90, 130, sale=120, stock=300, unit='ltr',
              desc='The original cola taste'),
            p('BVR-004', 'Coca-Cola 345ml Can', 'Cold Drinks', 'Coca-Cola',
              50, 75, stock=480, unit='ml'),
            p('BVR-005', '7Up 1.5 Litre', 'Cold Drinks', 'Pepsi',
              85, 125, stock=250, unit='ltr'),

            # ── Juices
            p('JCE-001', 'Shezan Mango Juice 1 Litre', 'Juices', 'Shezan',
              90, 130, sale=115, stock=200, featured=True, unit='ltr',
              desc='100% pure mango juice, no added sugar'),
            p('JCE-002', 'Shezan Apple Juice 200ml', 'Juices', 'Shezan',
              30, 45, stock=400, unit='ml'),
            p('JCE-003', 'Nestle Fruita Vitals Mango 200ml', 'Juices', 'Nestle',
              35, 55, stock=350, unit='ml'),

            # ── Tea & Coffee
            p('TEA-001', 'Tapal Danedar 900g', 'Tea & Coffee', 'Tapal',
              700, 950, featured=True, stock=150, unit='g',
              desc='Pakistan\'s most loved strong black tea'),
            p('TEA-002', 'Lipton Yellow Label 190g', 'Tea & Coffee', 'Lipton',
              380, 520, sale=480, stock=180, unit='g'),
            p('TEA-003', 'Tapal Family Mixture 450g', 'Tea & Coffee', 'Tapal',
              360, 490, stock=160, unit='g'),
            p('TEA-004', 'Nestle Coffee 100g', 'Tea & Coffee', 'Nestle',
              580, 780, stock=100, unit='g'),

            # ── Water
            p('WTR-001', 'Nestle Pure Life 1.5L', 'Water', 'Nestle',
              30, 50, stock=500, unit='ltr'),
            p('WTR-002', 'Nestle Pure Life 600ml', 'Water', 'Nestle',
              18, 30, stock=600, unit='ml'),

            # ── Milk
            p('MLK-001', 'Olpers Full Cream Milk 1 Litre', 'Milk', 'Olpers',
              140, 185, featured=True, stock=200, unit='ltr',
              desc='Fresh UHT full cream milk, rich in calcium'),
            p('MLK-002', 'Nestle Milkpak 1 Litre', 'Milk', 'Nestle',
              138, 180, stock=220, unit='ltr'),
            p('MLK-003', 'Olpers Lite Milk 1 Litre', 'Milk', 'Olpers',
              138, 180, sale=165, stock=150, unit='ltr',
              desc='Low fat UHT milk for a healthier choice'),

            # ── Yogurt & Cream
            p('YGT-001', 'Nestle Yogurt 400g', 'Yogurt & Cream', 'Nestle',
              90, 130, stock=180, unit='g'),
            p('YGT-002', 'Olpers Cream 200ml', 'Yogurt & Cream', 'Olpers',
              95, 135, stock=160, unit='ml'),

            # ── Butter & Cheese
            p('CHZ-001', 'Olpers Butter 200g', 'Butter & Cheese', 'Olpers',
              280, 380, featured=True, stock=120, unit='g'),
            p('CHZ-002', 'Nestle Cheddar Cheese Slices 200g', 'Butter & Cheese', 'Nestle',
              350, 480, sale=440, stock=100, unit='g'),

            # ── Bread & Roti
            p('BRD-001', 'Dawn Sandwich Bread', 'Bread & Roti', 'Dawn Bread',
              75, 110, featured=True, stock=200, unit='pcs',
              desc='Soft sandwich bread, freshly baked'),
            p('BRD-002', 'Dawn Burger Buns 6pcs', 'Bread & Roti', 'Dawn Bread',
              80, 115, stock=180, unit='pack'),

            # ── Biscuits
            p('BSC-001', 'Gourmet Chocolate Cream Biscuits 100g', 'Biscuits & Cookies', 'Gourmet',
              50, 75, stock=400, unit='g'),
            p('BSC-002', 'Gourmet Zeera Biscuits 80g', 'Biscuits & Cookies', 'Gourmet',
              40, 60, stock=350, unit='g'),

            # ── Chips
            p('CHP-001', 'Lays Classic Salted 34g', 'Chips & Crisps', 'Lays',
              35, 55, featured=True, stock=500, unit='g',
              desc='Crispy potato chips with a perfect dash of salt'),
            p('CHP-002', 'Lays Masala 34g', 'Chips & Crisps', 'Lays',
              35, 55, sale=50, stock=480, unit='g'),
            p('CHP-003', 'Pringles Original 165g', 'Chips & Crisps', 'Pringles',
              320, 450, stock=200, unit='g'),

            # ── Shampoo
            p('SHP-001', 'Sunsilk Soft & Smooth Shampoo 360ml', 'Shampoo & Hair Care', 'Sunsilk',
              380, 520, featured=True, sale=480, stock=150, unit='ml',
              desc='Nourishing shampoo for soft, silky hair'),
            p('SHP-002', 'Head & Shoulders Anti-Dandruff 360ml', 'Shampoo & Hair Care', 'Head & Shoulders',
              420, 580, stock=130, unit='ml'),

            # ── Soap
            p('SOP-001', 'Lux Soft Touch Soap 150g', 'Soap & Body Wash', 'Unilever',
              65, 95, stock=400, unit='g'),
            p('SOP-002', 'Lifebuoy Total 10 Soap 120g', 'Soap & Body Wash', 'Unilever',
              55, 80, stock=450, unit='g'),

            # ── Oral Care
            p('ORL-001', 'Colgate Total Toothpaste 75ml', 'Oral Care', 'Colgate',
              130, 185, featured=True, stock=300, unit='ml',
              desc='12-hour protection against germs and cavities'),
            p('ORL-002', 'Colgate Max Fresh 100ml', 'Oral Care', 'Colgate',
              140, 195, sale=175, stock=280, unit='ml'),

            # ── Detergents
            p('DET-001', 'Surf Excel Easy Wash 1kg', 'Detergents', 'Surf Excel',
              380, 520, featured=True, stock=200, unit='kg',
              desc='Removes tough stains in a single wash'),
            p('DET-002', 'Surf Excel Easy Wash 500g', 'Detergents', 'Surf Excel',
              200, 275, stock=280, unit='g'),

            # ── Dishwash
            p('DSH-001', 'Vim Dishwash Bar 250g', 'Dishwash', 'Vim',
              55, 80, stock=350, unit='g'),
            p('DSH-002', 'Vim Dishwash Liquid 400ml', 'Dishwash', 'Vim',
              160, 220, sale=200, stock=200, unit='ml'),

            # ── Tissues
            p('TSS-001', 'Nestle Tissues Box 100 Sheets', 'Tissues & Paper', 'Nestle',
              90, 130, stock=250, unit='box'),

            # ── Frozen
            p('FRZ-001', 'Chicken Nuggets 400g', 'Frozen Foods', 'Gourmet',
              380, 520, featured=True, sale=480, stock=120, unit='g',
              desc='Crispy golden chicken nuggets, ready in minutes'),
            p('FRZ-002', 'Beef Burger Patties 400g', 'Frozen Foods', 'Gourmet',
              420, 580, stock=100, unit='g'),

            # ── Fruits & Vegetables
            p('FRV-001', 'Fresh Tomatoes 1kg', 'Fruits & Vegetables', 'Gourmet',
              60, 90, stock=150, unit='kg',
              desc='Farm-fresh ripe tomatoes'),
            p('FRV-002', 'Bananas 1kg', 'Fruits & Vegetables', 'Gourmet',
              70, 100, stock=120, unit='kg'),
            p('FRV-003', 'Apples 1kg', 'Fruits & Vegetables', 'Gourmet',
              200, 280, sale=250, featured=True, stock=100, unit='kg',
              desc='Crisp and sweet fresh apples'),
            p('FRV-004', 'Onions 1kg', 'Fruits & Vegetables', 'Gourmet',
              40, 60, stock=200, unit='kg'),
            p('FRV-005', 'Potatoes 1kg', 'Fruits & Vegetables', 'Gourmet',
              45, 65, stock=200, unit='kg'),
        ]
