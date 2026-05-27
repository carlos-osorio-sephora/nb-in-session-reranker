import random
import numpy as np


def generate_sample_products(n=100):
    brands = [
        'NARS', 'Lancôme', 'Estée Lauder', 'Too Faced', 'MAC Cosmetics',
        'Fenty Beauty', 'Rare Beauty', 'Charlotte Tilbury', 'Dior', 'YSL',
        'Huda Beauty', 'Anastasia Beverly Hills', 'Urban Decay', 'Tarte', 'Benefit',
    ]
    first_level = ['Makeup', 'Skincare', 'Fragrance', 'Hair', 'Tools']
    second_level = {
        'Makeup': ['Face', 'Eye', 'Lip', 'Cheek'],
        'Skincare': ['Cleansers', 'Moisturizers', 'Treatments', 'Masks'],
        'Fragrance': ['Perfume', 'Body Spray'],
        'Hair': ['Shampoo', 'Conditioner', 'Styling'],
        'Tools': ['Brushes', 'Sponges', 'Accessories'],
    }
    third_level = {
        'Face': ['Foundation', 'Concealer', 'Powder', 'Primer'],
        'Eye': ['Eyeshadow', 'Mascara', 'Eyeliner', 'Brow'],
        'Lip': ['Lipstick', 'Lip Gloss', 'Lip Liner'],
        'Cheek': ['Blush', 'Bronzer', 'Highlighter'],
        'Cleansers': ['Face Wash', 'Cleansing Oil', 'Micellar Water'],
        'Moisturizers': ['Day Cream', 'Night Cream', 'Face Oil'],
        'Treatments': ['Serums', 'Toners', 'Exfoliants'],
        'Masks': ['Sheet Mask', 'Clay Mask', 'Peel-Off'],
        'Perfume': ['Eau de Parfum', 'Eau de Toilette'],
        'Body Spray': ['Body Mist'],
        'Shampoo': ['Moisturizing', 'Volumizing'],
        'Conditioner': ['Deep Conditioner', 'Leave-In'],
        'Styling': ['Hair Spray', 'Gel', 'Mousse'],
        'Brushes': ['Face Brush', 'Eye Brush'],
        'Sponges': ['Beauty Blender'],
        'Accessories': ['Tweezers', 'Lash Curler'],
    }

    products = {}
    for i in range(n):
        pid = f"P{str(i).zfill(5)}"
        brand = random.choice(brands)
        first = random.choice(first_level)
        second = random.choice(second_level[first])
        third = random.choice(third_level.get(second, ['General']))
        products[pid] = {
            'product_name': f"{brand} {third}",
            'brand_name': brand,
            'first_level_category': first,
            'second_level_category': second,
            'third_level_category': third,
            'price': round(random.uniform(15, 120), 2),
        }
    return products


def generate_sample_banners(n=20):
    brands = [
        'NARS', 'Lancôme', 'Estée Lauder', 'Too Faced', 'MAC Cosmetics',
        'Fenty Beauty', 'Rare Beauty', 'Charlotte Tilbury',
    ]
    categories = ['Foundation', 'Eyeshadow', 'Lipstick', 'Mascara', 'Serums',
                  'Day Cream', 'Blush', 'Highlighter', 'Concealer']
    worlds = ['Makeup', 'Skincare', 'Fragrance']
    banner_types = ['promotion', 'engagement', 'brand']
    promo_types = ['rewards', 'sale', 'gifts', 'new_arrival']

    banners = {}
    for i in range(n):
        bid = f"BNR{str(i).zfill(4)}"
        n_brands = random.randint(0, 3)
        mentioned_brands = random.sample(brands, min(n_brands, len(brands))) if n_brands > 0 else []
        mentioned_categories = random.sample(categories, random.randint(1, 4))
        mentioned_worlds = random.sample(worlds, random.randint(1, 2))
        product_ids = (
            [f"P{str(random.randint(0, 99)).zfill(5)}" for _ in range(random.randint(2, 5))]
            if random.random() > 0.3 else None
        )
        banners[bid] = {
            'banner_type': random.choice(banner_types),
            'promo_type': random.choice(promo_types),
            'mentioned_brands': np.array(mentioned_brands, dtype=object),
            'mentioned_categories': np.array(mentioned_categories, dtype=object),
            'product_ids': np.array(product_ids, dtype=object) if product_ids else None,
            'mentioned_worlds': np.array(mentioned_worlds, dtype=object),
        }
    return banners
