"""
Viewer Functions (General/Public Access)
"""

from db_connection import execute_query
from utils import *


def viewer_menu(user_id):
    """Main viewer menu"""
    while True:
        print_header(f"[General (Viewer)] - {user_id}")
        print("1) Browse Product Types")
        print("2) Generate Ingredient List")
        print("3) (Grad) Compare Two Products for Incompatibilities")
        print("0) Logout")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            print("\n")
            browse_products()
        elif choice == '2':
            print("\n")
            generate_ingredient_list()
        elif choice == '3':
            print("\n")
            compare_products()
        else:
            print("Invalid choice!")

def browse_products():
    """Browse available products"""
    print_header("Browse Product Types")
    print("1) View All Products")
    print("2) View by Category")
    print("3) View by Manufacturer")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == '1':
        products = execute_query("""
            SELECT p.product_id, p.product_number, p.name, c.name AS category,
                   CONCAT(u.first_name, ' ', u.last_name) AS manufacturer
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            JOIN User u ON p.manufacturer_id = u.user_id
            ORDER BY c.name, p.name
        """, fetch=True)
        
        print("\nAll Products:")
        print_table(['ID', 'Number', 'Name', 'Category', 'Manufacturer'], products)
    
    elif choice == '2':
        # Show categories
        categories = execute_query("SELECT * FROM Category", fetch=True)
        print("\nCategories:")
        print_table(['ID', 'Name'], categories)
        
        category_id = get_number_input("\nCategory ID: ")
        
        products = execute_query("""
            SELECT p.product_id, p.product_number, p.name,
                   CONCAT(u.first_name, ' ', u.last_name) AS manufacturer
            FROM Product p
            JOIN User u ON p.manufacturer_id = u.user_id
            WHERE p.category_id = %s
            ORDER BY p.name
        """, (category_id,), fetch=True)
        
        print(f"\nProducts in Category:")
        print_table(['ID', 'Number', 'Name', 'Manufacturer'], products)
    
    elif choice == '3':
        # Show manufacturers
        manufacturers = execute_query("""
            SELECT user_id, CONCAT(first_name, ' ', last_name) AS name
            FROM User
            WHERE user_type = 'MANUFACTURER'
        """, fetch=True)
        
        print("\nManufacturers:")
        print_table(['ID', 'Name'], manufacturers)
        
        manufacturer_id = input("\nEnter manufacturer ID: ").strip()
        
        products = execute_query("""
            SELECT p.product_id, p.product_number, p.name, c.name AS category
            FROM Product p
            JOIN Category c ON p.category_id = c.category_id
            WHERE p.manufacturer_id = %s
            ORDER BY p.name
        """, (manufacturer_id,), fetch=True)
        
        print(f"\nProducts by Manufacturer:")
        print_table(['ID', 'Number', 'Name', 'Category'], products)


def generate_ingredient_list():
    """Generate flattened ingredient list for a product batch"""
    print_header("Generate Ingredient List")
    
    # Show all product batches
    batches = execute_query("""
        SELECT pb.lot_number, p.name AS product_name, pb.produced_at, pb.expiration_date
        FROM ProductBatch pb
        JOIN Product p ON pb.product_id = p.product_id
        ORDER BY pb.produced_at DESC
    """, fetch=True)
    
    print("\nAvailable Product Batches:")
    print_table(['Lot Number', 'Product', 'Produced', 'Expires'], batches)
    
    # Get user input for lot number
    lot_number = input("\nEnter product batch lot number: ").strip()
    
    # Get ingredients from actual consumption for this specific batch
    ingredients = execute_query("""
        SELECT 
            i.ingredient_id,
            i.name AS ingredient_name,
            i.type,
            pc.qty AS quantity_used
        FROM ProductionConsumption pc
        JOIN IngredientBatch ib ON pc.ingredient_lot = ib.lot_number
        JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
        WHERE pc.product_batch = %s
        ORDER BY pc.qty DESC, i.name
    """, (lot_number,), fetch=True)
    
    if ingredients:
        print(f"\nIngredient List for Batch {lot_number} (ordered by quantity, largest first):")
        print_table(['ID', 'Ingredient', 'Type', 'Qty Used (oz)'], ingredients)
    else:
        print("\n No ingredients found for this batch or batch doesn't exist.")

def compare_products():
    """(Grad) Compare two products for ingredient incompatibilities"""
    print_header("(Grad) Compare Two Product Types for Incompatibilities")
    
    # Show all products
    products = execute_query("""
        SELECT p.product_id, p.product_number, p.name
        FROM Product p
        ORDER BY p.name
    """, fetch=True)
    
    print("\nAvailable Products:")
    print_table(['ID', 'Number', 'Name'], products)
    
    product1_id = get_number_input("\nEnter First Product ID: ")
    product2_id = get_number_input("Enter Second Product ID: ")
    
    # Step 1: Get all ingredients from product 1
    product1_ingredients = execute_query("""
        SELECT DISTINCT ingredient_id
        FROM ProductBOM
        WHERE product_id = %s
    """, (product1_id,), fetch=True)
    
    # Step 2: Get all ingredients from product 2
    product2_ingredients = execute_query("""
        SELECT DISTINCT ingredient_id
        FROM ProductBOM
        WHERE product_id = %s
    """, (product2_id,), fetch=True)
    
    # Step 3: Combine ingredient IDs into sets (union)
    ing_set_1 = {item['ingredient_id'] for item in product1_ingredients}
    ing_set_2 = {item['ingredient_id'] for item in product2_ingredients}
    all_ingredients = ing_set_1.union(ing_set_2)  # Union of both sets
    
    # Step 4: Check for conflicts between any pairs in the combined set
    conflicts_found = []
    
    for ing_a in all_ingredients:
        for ing_b in all_ingredients:
            if ing_a >= ing_b:  # Avoid duplicates and self-comparison
                continue
            
            # Check if this pair has a conflict
            conflict = execute_query("""
                SELECT cp.reason, cp.severity, 
                       ia.name AS ingredient_a_name,
                       ib.name AS ingredient_b_name
                FROM ConflictPairs cp
                JOIN Ingredient ia ON cp.ingredient_a = ia.ingredient_id
                JOIN Ingredient ib ON cp.ingredient_b = ib.ingredient_id
                WHERE (cp.ingredient_a = %s AND cp.ingredient_b = %s)
                   OR (cp.ingredient_a = %s AND cp.ingredient_b = %s)
            """, (ing_a, ing_b, ing_b, ing_a), fetch=True)
            
            if conflict:
                conflicts_found.append({
                    'ingredient_a': conflict[0]['ingredient_a_name'],
                    'ingredient_b': conflict[0]['ingredient_b_name'],
                    'reason': conflict[0]['reason'],
                    'severity': conflict[0]['severity']
                })
    
    # Step 5: Display results
    if conflicts_found:
        print("\nINCOMPATIBILITIES DETECTED!")
        print_table(['Ingredient A', 'Ingredient B', 'Reason', 'Severity'], conflicts_found)
    else:
        print("\n No incompatibilities found between these products.\n")