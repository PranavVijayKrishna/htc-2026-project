import json;
from collections import namedtuple;

ProductFilterResult = namedtuple('ProductFilterResults', ['passed', 'reason', 'flag'])

def load_products(path="backend/temp_data/products.json"):
    with open(path) as file:
        return json.load(file)

HIGH_TARIFF_COUNTRIES = ["China", "Russia", "Vietnam"]
FDA_BANNED = ["ephedra", "aristolochic acid"]

MIN_SHELF_LIFE = 12

def check_shelf_life(product):
    shelf_life = product['shelf_life_months']
    if shelf_life > MIN_SHELF_LIFE:
        return ProductFilterResult(passed=True, reason=None, flag=None)
    else:
        return ProductFilterResult(passed=False, reason=f'Shelf life {shelf_life} is less than {MIN_SHELF_LIFE}', flag=None)
    
def check_fda_banned(product):
    ingredients = product['ingredients']
    banned_ingredients_present = []
    for ingredient in ingredients:
        if ingredient in FDA_BANNED:
            banned_ingredients_present.append(ingredient)
    
    if banned_ingredients_present:
        return ProductFilterResult(passed=False, reason=f'Banned ingredients {banned_ingredients_present} present', flag=None)
    else:
        return ProductFilterResult(passed=True, reason=None, flag=None)
    
def check_origin_warning(product):
    origin = product['country_of_origin']
    if origin in HIGH_TARIFF_COUNTRIES:
        return ProductFilterResult(passed=True, reason=None, flag=f'Warning country: {origin}')
    else:
        return ProductFilterResult(passed=True, reason=None, flag=None)
    
def run_filter(product):
    shelf_life_result = check_shelf_life(product)
    fda_result = check_fda_banned(product)
    origin_result = check_origin_warning(product)

    return (shelf_life_result, fda_result, origin_result)


if __name__ == '__main__':
    all_product_info = load_products()
    for product in all_product_info:
        results = run_filter(product)
        print(results)
