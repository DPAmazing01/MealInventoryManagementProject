"""
Supplier Functions
"""

from db_connection import execute_query
from utils import *
from datetime import datetime, timedelta

def ingredient_exists(ingredient_id):
    """Check if ingredient exists in database"""
    result = execute_query(
        "SELECT ingredient_id FROM Ingredient WHERE ingredient_id = %s",
        (ingredient_id,),
        fetch=True
    )
    return bool(result)

def supplier_menu(user_id):
    """Main supplier menu"""
    # Get supplier_id from user_id
    supplier_data = execute_query(
        "SELECT supplier_id FROM Supplier WHERE user_id = %s",
        (user_id,), fetch=True
    )
    
    if not supplier_data:
        print("\n Supplier account not found!")
        return
    
    supplier_id = supplier_data[0]['supplier_id']
    
    while True:
        print_header(f"[Supplier] - {user_id}")
        print("1) Manage Ingredients Supplied")
        print("2) Maintain Formulations")
        print("3) Create Ingredient Batch")
        print("4) (Grad) Maintain Do-Not-Combine List")
        print("0) Logout")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            manage_ingredients_supplied(supplier_id)
        elif choice == '2':
            maintain_formulations(supplier_id)
        elif choice == '3':
            create_ingredient_batch(supplier_id)
        elif choice == '4':
            maintain_do_not_combine(supplier_id)
        else:
            print("Invalid choice!")

def manage_ingredients_supplied(supplier_id):
    """Declare which ingredients this supplier can supply"""
    print_header("Declare Ingredients Supplied")
    
    # Show all ingredients
    ingredients = execute_query("SELECT ingredient_id, name, type FROM Ingredient", fetch=True)
    print("\nAll Ingredients:")
    print_table(['ID', 'Name', 'Type'], ingredients)
    
    # Show currently supplied
    supplied = execute_query("""
        SELECT i.ingredient_id, i.name
        FROM Ingredient i
        JOIN SupplierIngredient si ON i.ingredient_id = si.ingredient_id
        WHERE si.supplier_id = %s AND si.can_supply = TRUE
    """, (supplier_id,), fetch=True)
    
    if supplied:
        print("\nCurrently Supplied:")
        print_table(['ID', 'Name'], supplied)
    
    ingredient_input = input("\nEnter ingredient ID to add/update ('done' or 'q' to cancel): ").strip().lower()
    
    if ingredient_input in ('done', 'q'):
        return
        
    try:
        ingredient_id = int(ingredient_input)
        if not ingredient_exists(ingredient_id):
            print(f"\nIngredient ID {ingredient_id} does not exist.")
            return
    except ValueError:
        print("\nInvalid input. Please enter a valid ingredient ID, 'done', or 'q'.")
        return
    
    can_supply = input("Can supply? (y/n): ").strip().lower() == 'y'
    
    # Check if already exists
    existing = execute_query("""
        SELECT * FROM SupplierIngredient 
        WHERE supplier_id = %s AND ingredient_id = %s
    """, (supplier_id, ingredient_id), fetch=True)
    
    if existing:
        query = """
            UPDATE SupplierIngredient 
            SET can_supply = %s
            WHERE supplier_id = %s AND ingredient_id = %s
        """
        params = (can_supply, supplier_id, ingredient_id)
    else:
        query = """
            INSERT INTO SupplierIngredient (supplier_id, ingredient_id, can_supply)
            VALUES (%s, %s, %s)
        """
        params = (supplier_id, ingredient_id, can_supply)
    
    if execute_query(query, params):
        print(f"\nIngredient supply status updated!\n")


def maintain_formulations(supplier_id):
    """Maintain formulations for ingredients"""
    print_header("Maintain Formulations")
    
    # Show supplier's ingredients
    ingredients = execute_query("""
        SELECT i.ingredient_id, i.name, i.type
        FROM Ingredient i
        JOIN SupplierIngredient si ON i.ingredient_id = si.ingredient_id
        WHERE si.supplier_id = %s AND si.can_supply = TRUE
    """, (supplier_id,), fetch=True)
    
    print("\nYour Supplied Ingredients:")
    print_table(['ID', 'Name', 'Type'], ingredients)
    
    ingredient_id = get_number_input("\nEnter ingredient ID: ")
    
    # Check if supplier can supply this
    can_supply = execute_query("""
        SELECT can_supply FROM SupplierIngredient
        WHERE supplier_id = %s AND ingredient_id = %s
    """, (supplier_id, ingredient_id), fetch=True)
    
    if not can_supply or not can_supply[0]['can_supply']:
        print("\nYou don't supply this ingredient!\n")
        return
    
    # Get formulation details
    print("\nEnter Formulation Details...")
    
    # Get next version number (COALESCE handles NULL when no recipes exist)
    max_version = execute_query("""
        SELECT COALESCE(MAX(version_no), 0) as max_ver 
        FROM IngredientFormulation 
        WHERE ingredient_id = %s AND supplier_id = %s
    """, (ingredient_id, supplier_id), fetch=True)
    version_no = max_version[0]['max_ver'] + 1
    
    effective_start = get_date_input("Enter effective Start Date (YYYY-MM-DD): ")
    effective_end = get_date_input("Enter effective End Date (YYYY-MM-DD, Enter for NULL): ", allow_empty=True)
    price_per_pack = get_number_input("Enter price per pack: ", allow_decimal=True)
    pack_size = get_number_input("Enter pack size (oz): ", allow_decimal=True)
    is_active = input("Is active? (y/n): ").strip().lower() == 'y'
    
    # Insert formulation
    query = """
        INSERT INTO IngredientFormulation 
        (ingredient_id, supplier_id, version_no, effective_start, effective_end, 
         price_per_pack, pack_size, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (ingredient_id, supplier_id, version_no, effective_start, effective_end,
              price_per_pack, pack_size, is_active)
    
    # execute_query returns the lastrowid for INSERT queries!
    formulation_id = execute_query(query, params)  # Capture the return value!

    if not formulation_id or formulation_id is True:  # Validate it
        print("\nFailed to create formulation!")
        return
    
    # Get ingredient type
    ing_type = execute_query(
        "SELECT type FROM Ingredient WHERE ingredient_id = %s",
        (ingredient_id,), fetch=True
    )[0]['type']
    
    # If compound, add materials (the rest of the code is here, using the valid formulation_id)
    if ing_type == 'COMPOUND':
        print("\n--- Add Materials (atomic ingredients only) ---")
        
        # Show atomic ingredients
        atomics = execute_query(
            "SELECT ingredient_id, name FROM Ingredient WHERE type = 'ATOMIC'",
            fetch=True
        )
        print("\nAvailable Atomic Ingredients:")
        print_table(['ID', 'Name'], atomics)
        
        print("\nAdd materials...")
        while True:
            material_input = input("Enter material ingredient ID ('done' or 'q' to finish): ").strip().lower()
            
            if material_input in ('done', 'q'):
                break
            
            try:
                material_id = int(material_input)
            except ValueError:
                print("Invalid input. Please enter a valid Ingredient ID, 'done', or 'q'.")
                continue # Go back to the start of the loop
            
            qty = get_number_input("Enter quantity (oz): ", allow_decimal=True)
            
            query = """
                INSERT INTO FormulationMaterials (formulation_id, ingredient_id, qty)
                VALUES (%s, %s, %s)
            """
            execute_query(query, (formulation_id, material_id, qty))
    
    print(f"\nFormulation v{version_no} created successfully!\n")

def create_ingredient_batch(supplier_id):
    """Create an ingredient batch"""
    print_header("Create Ingredient Batch")
    
    # Show supplier's ingredients
    ingredients = execute_query("""
        SELECT i.ingredient_id, i.name
        FROM Ingredient i
        JOIN SupplierIngredient si ON i.ingredient_id = si.ingredient_id
        WHERE si.supplier_id = %s AND si.can_supply = TRUE
    """, (supplier_id,), fetch=True)
    
    print("\nYour Supplied Ingredients:")
    print_table(['ID', 'Name'], ingredients)
    
    ingredient_id = get_number_input("\nEnter ingredient ID: ")
    
    # Verify supplier can supply this ingredient
    can_supply = execute_query("""
        SELECT can_supply FROM SupplierIngredient
        WHERE supplier_id = %s AND ingredient_id = %s
    """, (supplier_id, ingredient_id), fetch=True)
    
    if not can_supply or not can_supply[0]['can_supply']:
        print("\nYou don't supply this ingredient!")
        return
    
    quantity = get_number_input("Enter quantity (oz): ", allow_decimal=True)
    unit_cost = get_number_input("Enter unit cost per oz: ", allow_decimal=True)
    intake_date = get_date_input("Enter Intake Date (YYYY-MM-DD): ")
    expiration_date = get_date_input("Enter Expiration Date (YYYY-MM-DD): ")
    
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
        lot = execute_query("""
            SELECT lot_number FROM IngredientBatch 
            WHERE ingredient_id=%s AND supplier_id=%s 
            ORDER BY lot_number DESC LIMIT 1
        """, (ingredient_id, supplier_id), fetch=True)
        
        print(f"\nIngredient batch created successfully!")
        print(f" Lot Number: {lot[0]['lot_number']}\n")

def maintain_do_not_combine(supplier_id):
    """(Grad) Maintain do-not-combine list for incompatible ingredients"""
    print_header("(Grad) Maintain Do-Not-Combine List")
    
    while True:
        # Show existing conflicts
        conflicts = execute_query("""
            SELECT cp.ingredient_a, ia.name AS ingredient_a_name,
                   cp.ingredient_b, ib.name AS ingredient_b_name,
                   cp.severity, cp.reason
            FROM ConflictPairs cp
            JOIN Ingredient ia ON cp.ingredient_a = ia.ingredient_id
            JOIN Ingredient ib ON cp.ingredient_b = ib.ingredient_id
            ORDER BY cp.severity DESC, ia.name
        """, fetch=True)
        
        if conflicts:
            print("\nExisting Conflict Pairs:")
            print_table(['Ing A ID', 'Ingredient A', 'Ing B ID', 'Ingredient B', 'Severity', 'Reason'], 
                       conflicts)
        else:
            print("\nNo conflict pairs defined yet.")
        
        print("\nOptions:")
        print("1) Add Conflict Pair")
        print("2) Remove Conflict Pair")
        print("0) Back to Menu")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            add_conflict_pair()
        elif choice == '2':
            remove_conflict_pair()
        else:
            print("Invalid choice!")


def add_conflict_pair():
    """Add a new conflict pair"""
    print("\n--- Add Conflict Pair ---")
    
    # Show all ingredients
    ingredients = execute_query(
        "SELECT ingredient_id, name, type FROM Ingredient ORDER BY name",
        fetch=True
    )
    print("\nAvailable Ingredients:")
    print_table(['ID', 'Name', 'Type'], ingredients)
    
    ingredient_a = get_number_input("\nEnter first ingredient ID: ")
    ingredient_b = get_number_input("Enter second ingredient ID: ")

    if not ingredient_exists(ingredient_a):
        print(f"\nIngredient ID {ingredient_a} does not exist.")
        return
    if not ingredient_exists(ingredient_b):
        print(f"\nIngredient ID {ingredient_b} does not exist.")
        return
    if ingredient_a == ingredient_b:
        print("\nIngredients must be different!")
        return
    
    reason = input("Enter reason for incompatibility: ").strip()
    
    print("\nSeverity Level:")
    print("1) WARNING")
    print("2) CRITICAL")
    severity_choice = input("Enter choice (1 or 2): ").strip()
    if severity_choice == '1':
        severity = 'WARNING'
    elif severity_choice == '2':
        severity = 'CRITICAL'
    else:
        print("\nInvalid severity option")
        return
    
    # Insert conflict pair (trigger will handle ordering ingredient_a < ingredient_b)
    query = """
        INSERT INTO ConflictPairs (ingredient_a, ingredient_b, reason, severity)
        VALUES (%s, %s, %s, %s)
    """
    
    if execute_query(query, (ingredient_a, ingredient_b, reason, severity)):
        print("\nConflict pair added successfully!")


def remove_conflict_pair():
    """Remove an existing conflict pair"""
    print("\n--- Remove Conflict Pair ---")
    
    ingredient_a = get_number_input("\nEnter first ingredient ID: ")
    ingredient_b = get_number_input("Enter second ingredient ID: ")

    if not ingredient_exists(ingredient_a):
        print(f"\nIngredient ID {ingredient_a} does not exist.")
        return
    if not ingredient_exists(ingredient_b):
        print(f"\nIngredient ID {ingredient_b} does not exist.")
        return
    if ingredient_a == ingredient_b:
        print("\nIngredients must be different!")
        return
    exists_query = """
        SELECT 1 FROM ConflictPairs
        WHERE ingredient_a = LEAST(%s, %s)
          AND ingredient_b = GREATEST(%s, %s)
        LIMIT 1
    """
    exists = execute_query(
        exists_query,
        (ingredient_a, ingredient_b, ingredient_a, ingredient_b),
        fetch=True
    )
    if not exists:
        print("\nNo conflict pair exists with those ingredient IDs.")
        return
    
    # Need to check both orderings since trigger normalizes them
    query = """
        DELETE FROM ConflictPairs
        WHERE (ingredient_a = LEAST(%s, %s) AND ingredient_b = GREATEST(%s, %s))
    """
    
    if execute_query(query, (ingredient_a, ingredient_b, ingredient_a, ingredient_b)):
        print("\nConflict pair removed successfully!")