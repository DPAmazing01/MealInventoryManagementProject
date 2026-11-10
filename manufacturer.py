"""
Manufacturer Functions
"""

from db_connection import execute_query, call_procedure
from utils import *
from datetime import datetime, timedelta
from decimal import Decimal
import json

def manufacturer_menu(user_id):
    """Main manufacturer menu"""
    while True:
        print_header(f"[Manufacturer] - {user_id}")
        print("1) Define/Update Product")
        print("2) Define/Update Product BOM")
        print("3) Record Ingredient Receipt")
        print("4) Create Product Batch")
        print("5) Reports")
        print("6) (Grad) Recall/Traceability")
        print("0) Logout")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            define_product(user_id)
        elif choice == '2':
            define_product_bom(user_id)
        elif choice == '3':
            record_ingredient_receipt()
        elif choice == '4':
            create_product_batch(user_id)
        elif choice == '5':
            reports_menu()
        elif choice == '6':
            recall_traceability()
        else:
            print("Invalid choice!")

def define_product(manufacturer_id):
    """Define or update a product"""
    print_header("Define/Update Product")
    
    # Show categories
    categories = execute_query("SELECT * FROM Category", fetch=True)
    print("\nAvailable Categories:")
    print_table(['Category ID', 'Name'], categories)
    
    # Get product details
    product_number = input("\nProduct Number (e.g., P-100): ").strip()
    name = input("Product Name: ").strip()
    category_id = get_number_input("Category ID: ")
    description = input("Description (optional): ").strip() or None
    standard_batch_units = get_number_input("Standard Batch Units: ")
    
    # Check if product exists
    existing = execute_query(
        "SELECT product_id FROM Product WHERE product_number = %s",
        (product_number,), fetch=True
    )
    
    if existing:
        # Update
        query = """
            UPDATE Product 
            SET name=%s, category_id=%s, description=%s, standard_batch_units=%s
            WHERE product_number=%s AND manufacturer_id=%s
        """
        params = (name, category_id, description, standard_batch_units, product_number, manufacturer_id)
        if execute_query(query, params):
            print(f"\nProduct '{name}' updated successfully!")
    else:
        # Insert
        query = """
            INSERT INTO Product (product_number, name, category_id, manufacturer_id, 
                               description, standard_batch_units)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (product_number, name, category_id, manufacturer_id, description, standard_batch_units)
        if execute_query(query, params):
            print(f"\nProduct '{name}' created successfully!\n")

def define_product_bom(manufacturer_id):
    """Define or update product BOM (Recipe Plan)"""
    print_header("Define/Update Product BOM")
    
    # Show manufacturer's products
    products = execute_query(
        "SELECT product_id, product_number, name FROM Product WHERE manufacturer_id = %s",
        (manufacturer_id,), fetch=True
    )
    print("\nYour Products:")
    print_table(['Product ID', 'Product Number', 'Name'], products)
    
    product_id = get_number_input("\nEnter Product ID: ")
    
    # Check ownership
    owner = execute_query(
        "SELECT manufacturer_id FROM Product WHERE product_id = %s",
        (product_id,), fetch=True
    )
    if not owner or owner[0]['manufacturer_id'] != manufacturer_id:
        print("\n You don't own this product!")
        return
    
    # Get version number (COALESCE handles NULL when no recipes exist)
    max_version = execute_query(
        "SELECT COALESCE(MAX(version_no), 0) as max_ver FROM RecipePlan WHERE product_id = %s",
        (product_id,), fetch=True
    )
    version_no = max_version[0]['max_ver'] + 1
    
    notes = input("Recipe Notes (optional): ").strip() or None
    
    # Create recipe plan
    query = """
        INSERT INTO RecipePlan (product_id, version_no, creation_date, is_active, notes)
        VALUES (%s, %s, CURDATE(), TRUE, %s)
    """

    recipe_id = execute_query(query, (product_id, version_no, notes))
    
    # Show available ingredients
    ingredients = execute_query("SELECT ingredient_id, name, type FROM Ingredient", fetch=True)
    print("\nAvailable Ingredients:")
    print_table(['ID', 'Name', 'Type'], ingredients)
    
    # Add ingredients to BOM
    print("\nAdd ingredients to BOM...")
    while True:
        ingredient_input = input("Enter ingredient ID (or 'done'/'q' to finish): ").strip().lower()

        if ingredient_input in ['done', 'q', '']:
            break

        try:
            ingredient_id = int(ingredient_input)
        except ValueError:
            print(" Please enter a valid number or 'done' to finish")
            continue
    
        qty = get_number_input("Quantity (oz): ", allow_decimal=True)
    
        query = """
            INSERT INTO ProductBOM (product_id, ingredient_id, qty, recipe_id)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(query, (product_id, ingredient_id, qty, recipe_id))
    
    print(f"\nRecipe Plan v{version_no} created successfully!\n")

def record_ingredient_receipt():
    """Record ingredient batch receipt"""
    print_header("Record Ingredient Receipt")
    
    # Show ingredients
    ingredients = execute_query("SELECT ingredient_id, name FROM Ingredient", fetch=True)
    print("\nAvailable Ingredients:")
    print_table(['ID', 'Name'], ingredients)
    
    ingredient_id = get_number_input("\nEnter ingredient ID: ")
    
    # Show suppliers for this ingredient
    suppliers = execute_query("""
        SELECT s.supplier_id, s.name 
        FROM Supplier s
        JOIN SupplierIngredient si ON s.supplier_id = si.supplier_id
        WHERE si.ingredient_id = %s AND si.can_supply = TRUE
    """, (ingredient_id,), fetch=True)
    
    if not suppliers:
        print("\nNo suppliers available for this ingredient!")
        return
    
    print("\nSuppliers for this ingredient:")
    print_table(['Supplier ID', 'Name'], suppliers)
    
    supplier_id = get_number_input("Enter supplier ID: ")
    quantity = get_number_input("Enter quantity (oz): ", allow_decimal=True)
    unit_cost = get_number_input("Enter unit cost: ", allow_decimal=True)
    intake_date = get_date_input("Enter intake date (YYYY-MM-DD): ")
    expiration_date = get_date_input("Enter expiration Date (YYYY-MM-DD): ")
    
    # Validate 90-day rule
    min_expiration = intake_date + timedelta(days=90)
    if expiration_date < min_expiration:
        print(f"\nRejected! Expiration date must be at least 90 days from intake.")
        print(f" Minimum allowed expiration: {min_expiration}")
        return
    
    # Insert batch (lot_number will be auto-generated by trigger)
    query = """
        INSERT INTO IngredientBatch 
        (ingredient_id, supplier_id, quantity, unit_cost, expiration_date, intake_date, on_hand_quantity)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (ingredient_id, supplier_id, quantity, unit_cost, expiration_date, intake_date, quantity)
    
    if execute_query(query, params):
        # Get the generated lot number
        lot = execute_query(
            "SELECT lot_number FROM IngredientBatch WHERE ingredient_id=%s AND supplier_id=%s ORDER BY intake_date DESC LIMIT 1",
            (ingredient_id, supplier_id), fetch=True
        )
        lot_number = lot[0]["lot_number"]

        # lot_number expected to be something like "B0012"
        print(f"\nIngredient batch created successfully!")
        print(f" Lot Number: {lot_number}\n")

def create_product_batch(manufacturer_id):
    """Create a product batch"""
    print_header("Create Product Batch")
    
    # Show manufacturer's products
    products = execute_query(
        "SELECT product_id, product_number, name, standard_batch_units FROM Product WHERE manufacturer_id = %s",
        (manufacturer_id,), fetch=True
    )
    print("\nYour Products:")
    print_table(['Product ID', 'Product Number', 'Name', 'Std Batch'], products)
    
    product_id = get_number_input("\nEnter product ID: ")
    
    # Get product details
    product = execute_query(
        "SELECT standard_batch_units FROM Product WHERE product_id = %s AND manufacturer_id = %s",
        (product_id, manufacturer_id), fetch=True
    )
    if not product:
        print("\n Product not found or not owned by you!")
        return
    
    std_batch = product[0]['standard_batch_units']
    
    # Show active recipes
    recipes = execute_query(
        "SELECT recipe_id, version_no, creation_date FROM RecipePlan WHERE product_id = %s AND is_active = TRUE",
        (product_id,), fetch=True
    )
    print("\nActive Recipes:")
    print_table(['Recipe ID', 'Version', 'Created'], recipes)
    
    recipe_id = get_number_input("Enter recipe ID: ")

    valid_ids = {r['recipe_id'] for r in recipes}
    if recipe_id not in valid_ids:
        print(f"\nError: Recipe ID {recipe_id} is not an active recipe for this product.")
        return
    
    produced_qty = get_number_input(f"Produced Quantity (multiple of {std_batch}): ")
    if produced_qty % std_batch != 0:
        print(f"\n Quantity must be a multiple of {std_batch}!")
        return
    
    produced_at = get_date_input("Production Date (YYYY-MM-DD): ")
    expiration_date = get_date_input("Expiration Date (YYYY-MM-DD): ")
    
    # Get BOM for this recipe
    bom = execute_query("""
        SELECT pb.ingredient_id, i.name, pb.qty
        FROM ProductBOM pb
        JOIN Ingredient i ON pb.ingredient_id = i.ingredient_id
        WHERE pb.product_id = %s AND (pb.recipe_id = %s OR pb.recipe_id IS NULL)
    """, (product_id, recipe_id), fetch=True)
    
    print("\nRequired Ingredients:")
    print_table(['ID', 'Name', 'Required Qty (oz)'], bom)
    
    # Select lots for each ingredient
    consumptions = []
    print("\nSelect ingredient lots to consume:")
    
    for item in bom:
        ingredient_id = item['ingredient_id']
        # Convert the scale factor to Decimal to avoid TypeError
        required_qty = item['qty'] * (Decimal(produced_qty) / Decimal(std_batch)) # Scale to batch size
        
        print(f"\n{item['name']} - Need {required_qty} oz")
        
        # Show available batches (FEFO - First Expired First Out)
        batches = execute_query("""
            SELECT lot_number, on_hand_quantity, unit_cost, expiration_date
            FROM IngredientBatch
            WHERE ingredient_id = %s 
              AND on_hand_quantity > 0 
              AND expiration_date >= CURDATE()
            ORDER BY expiration_date ASC
        """, (ingredient_id,), fetch=True)
        
        if not batches:
            print(f"  No available batches for {item['name']}!")
            return
        
        print_table(['Lot Number', 'On Hand', 'Unit Cost', 'Expires'], batches)
        
        remaining = required_qty
        for batch in batches:
            if remaining <= 0:
                break
            
            available = batch['on_hand_quantity']
            to_consume = min(remaining, available)
            
            consumptions.append({
                'lot': batch['lot_number'],
                'qty': float(to_consume)  # Convert Decimal to float for JSON
            })
            remaining -= to_consume
            print(f"Auto-selected: {batch['lot_number']} - {to_consume} oz")
        
        if remaining > 0:
            print(f"Insufficient quantity! Short by {remaining} oz")
            return
    
    # Create batch using stored procedure
    print(f"\nCreating product batch...")
    consumptions_json = json.dumps(consumptions)
    
    result = call_procedure('RecordProductionBatch', [
        product_id, manufacturer_id, recipe_id, produced_qty,
        produced_at, expiration_date, consumptions_json
    ])
    
    if result is not None:
        # Get the created batch
        batch = execute_query("""
            SELECT lot_number, total_batch_cost, per_unit_cost
            FROM ProductBatch
            WHERE product_id = %s AND manufacturer_id = %s
            ORDER BY lot_number DESC LIMIT 1
        """, (product_id, manufacturer_id), fetch=True)
        
        if batch:
            print(f"Product batch created successfully!")
            print(f" Lot Number: {batch[0]['lot_number']}")
            print(f" Total Cost: ${batch[0]['total_batch_cost']:.2f}")
            print(f" Per Unit Cost: ${batch[0]['per_unit_cost']:.4f}\n")

def reports_menu():
    """Reports submenu"""
    while True:
        print_header("Reports Menu")
        print("1) On-hand by Item/Lot")
        print("2) Nearly Out-of-Stock")
        print("3) Almost-Expired Ingredient Lots")
        print("4) Batch Cost Summary")
        print("0) Back")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            report_on_hand()
        elif choice == '2':
            report_nearly_out_of_stock()
        elif choice == '3':
            report_almost_expired()
        elif choice == '4':
            report_batch_cost()
        else:
            print("Invalid choice!")

def report_on_hand():
    """Report on-hand inventory"""
    print_header("On-Hand Inventory")
    
    result = execute_query("""
        SELECT ib.lot_number, i.name AS ingredient, s.name AS supplier,
               ib.on_hand_quantity, ib.expiration_date
        FROM IngredientBatch ib
        JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
        JOIN Supplier s ON ib.supplier_id = s.supplier_id
        WHERE ib.on_hand_quantity > 0
        ORDER BY i.name, ib.expiration_date
    """, fetch=True)
    
    print_table(['Lot Number', 'Ingredient', 'Supplier', 'On Hand', 'Expires'], result)

def report_nearly_out_of_stock():
    """Report nearly out-of-stock items"""
    print_header("Nearly Out-of-Stock Items")
    
    result = execute_query("""
        SELECT p.name AS product, p.standard_batch_units,
               SUM(ib.on_hand_quantity) AS total_on_hand
        FROM Product p
        LEFT JOIN ProductBOM pb ON p.product_id = pb.product_id
        LEFT JOIN IngredientBatch ib ON pb.ingredient_id = ib.ingredient_id
        GROUP BY p.product_id, p.name, p.standard_batch_units
        HAVING total_on_hand < p.standard_batch_units OR total_on_hand IS NULL
    """, fetch=True)
    
    print_table(['Product', 'Std Batch', 'Total On Hand'], result)

def report_almost_expired():
    """Report almost-expired batches (within 10 days)"""
    print_header("Almost-Expired Ingredient Lots")
    
    result = execute_query("""
        SELECT ib.lot_number, i.name AS ingredient, ib.on_hand_quantity,
               ib.expiration_date, DATEDIFF(ib.expiration_date, CURDATE()) AS days_until_expiry
        FROM IngredientBatch ib
        JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
        WHERE ib.on_hand_quantity > 0
          AND ib.expiration_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 10 DAY)
        ORDER BY ib.expiration_date
    """, fetch=True)
    
    print_table(['Lot Number', 'Ingredient', 'On Hand', 'Expires', 'Days Left'], result)

def report_batch_cost():
    """Report batch cost summary"""
    print_header("Batch Cost Summary")
    
    lot_number = input("\nEnter Product Lot Number (e.g., 100-MFG001-B0901): ").strip()
    
    result = execute_query("""
        SELECT lot_number, product_id, produced_qty, produced_at,
               total_batch_cost, per_unit_cost
        FROM ProductBatch
        WHERE lot_number = %s
    """, (lot_number,), fetch=True)
    
    if result:
        print_table(['Lot', 'Product ID', 'Qty', 'Produced', 'Total Cost', 'Unit Cost'], result)
        
        # Show consumption details
        consumption = execute_query("""
            SELECT pc.ingredient_lot, i.name AS ingredient, pc.qty,
                   ib.unit_cost, (pc.qty * ib.unit_cost) AS cost
            FROM ProductionConsumption pc
            JOIN IngredientBatch ib ON pc.ingredient_lot = ib.lot_number
            JOIN Ingredient i ON ib.ingredient_id = i.ingredient_id
            WHERE pc.product_batch = %s
        """, (lot_number,), fetch=True)
        
        print("\nIngredient Consumption:")
        print_table(['Ingredient Lot', 'Ingredient', 'Qty', 'Unit Cost', 'Total'], consumption)
    else:
        print("\n Batch not found!")

def recall_traceability():
    """Trace recall impacts"""
    print_header("Recall & Traceability")
    
    print("\n1) Trace by Ingredient ID")
    print("2) Trace by Lot Number")
    choice = input("\nEnter choice: ").strip()
    
    if choice == '1':
        ingredient_id = get_number_input("Enter ingredient ID: ")
        result = call_procedure('TraceRecall', [ingredient_id, None])
    elif choice == '2':
        lot_number = input("Enter ingredient Lot Number (e.g., 201-20-B0002): ").strip()
        result = call_procedure('TraceRecall', [None, lot_number])
    else:
        print("Invalid choice!")
        return
    
    if result:
        print("\nAffected Product Batches:")
        print_table(result[0].keys(), result)
    else:
        print("\nNo affected batches found or error occurred.")