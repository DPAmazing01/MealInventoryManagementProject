"""
Predefined Queries Module
"""

from db_connection import execute_query
from utils import print_header, print_table


def queries_menu():
    while True:
        print_header("Predefined Queries")
        print("1) List the ingredients and the lot number of the last batch of product type Steak Dinner (100) made by manufacturer MFG001.")
        print("2) For manufacturer MFG002, list all the suppliers that they have purchased from and the total amount of money they have spent with that supplier.")
        print("3) For product with lot number 100-MFG001-B0901, find the unit cost for that product.")
        print("4) Based on the ingredients currently in product lot number 100-MFG001-B0901, what are all ingredients that cannot be included (i.e. that are in conflict with the current ingredient list).")
        print("5) Which manufacturers have supplier Supplier B (21) NOT supplied to?")
        print("0) Back")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            query_1()
        elif choice == '2':
            query_2()
        elif choice == '3':
            query_3()
        elif choice == '4':
            query_4()
        elif choice == '5':
            query_5()
        else:
            print("Invalid choice!")

def query_1():
    """
    Query 1: List the ingredients and the lot number of the last batch of 
    product type Steak Dinner (100) made by manufacturer MFG001.
    """
    print_header("Query 1:")
    
    result = execute_query("""
        SELECT 
            i.name AS ingredient_name,
            pb.lot_number AS product_batch
        FROM ProductBatch pb
        JOIN ProductionConsumption pc 
              ON pb.lot_number = pc.product_batch
        JOIN IngredientBatch ib 
              ON pc.ingredient_lot = ib.lot_number
        JOIN Ingredient i 
              ON ib.ingredient_id = i.ingredient_id
        WHERE pb.product_id = 100
          AND pb.manufacturer_id = 'MFG001'
          AND pb.produced_at = (
                SELECT MAX(produced_at)
                FROM ProductBatch
                WHERE product_id = 100 AND manufacturer_id = 'MFG001'
          )
        ORDER BY i.name
    """, fetch=True)
    
    if result:
        print_table(['Ingredient Name', 'Product Batch'], result)
    else:
        print("\nNo data found.")


def query_2():
    """
    Query 2: For manufacturer MFG002, list all the suppliers that they have 
    purchased from and the total amount of money they have spent with that supplier.
    """
    print_header("Query 2:")
    
    result = execute_query("""
        SELECT 
            s.name AS supplier_name,
            ROUND(SUM(pc.qty * ib.unit_cost), 2) AS total_spent
        FROM ProductBatch pb
        JOIN ProductionConsumption pc 
              ON pb.lot_number = pc.product_batch
        JOIN IngredientBatch ib 
              ON pc.ingredient_lot = ib.lot_number
        JOIN Supplier s 
              ON ib.supplier_id = s.supplier_id
        WHERE pb.manufacturer_id = 'MFG002'
        GROUP BY s.supplier_id, s.name
        ORDER BY total_spent DESC
    """, fetch=True)
    
    if result:
        print_table(['Supplier Name', 'Total Spent ($)'], result)
    else:
        print("\nNo data found.")


def query_3():
    """
    Query 3: For product with lot number 100-MFG001-B0901, 
    find the unit cost for that product.
    """
    print_header("Query 3:")
    
    result = execute_query("""
        SELECT
            per_unit_cost
        FROM ProductBatch
        WHERE lot_number = '100-MFG001-B0901'
    """, fetch=True)
    
    if result:
        print_table(['Unit Cost'], result)
    else:
        print("\nProduct lot not found.")


def query_4():
    """
    Query 4: Based on the ingredients currently in product lot number 
    100-MFG001-B0901, what are all ingredients that cannot be included 
    (i.e. that are in conflict with the current ingredient list).
    """
    print_header("Query 4:")
    
    result = execute_query("""
        SELECT DISTINCT
            i_conflict.name AS conflicting_ingredient
        FROM ProductionConsumption pc
        JOIN IngredientBatch ib 
              ON pc.ingredient_lot = ib.lot_number
        JOIN ConflictPairs cp 
              ON cp.ingredient_a = ib.ingredient_id
                OR cp.ingredient_b = ib.ingredient_id
        JOIN Ingredient i_conflict 
              ON i_conflict.ingredient_id = 
                 CASE 
                   WHEN cp.ingredient_a = ib.ingredient_id THEN cp.ingredient_b
                   ELSE cp.ingredient_a
                 END
        WHERE pc.product_batch = '100-MFG001-B0901'
    """, fetch=True)
    
    if result:
        print_table(['Conflicting Ingredient'], result)
    else:
        print("\nNo conflicting ingredients found or batch doesn't exist.")


def query_5():
    """
    Query 5: Which manufacturers have supplier Supplier B (21) NOT supplied to?
    """
    print_header("Query 5: Manufacturers Not Supplied By Supplier")
    
    result = execute_query("""
        SELECT DISTINCT
               u.first_name,
               u.last_name
        FROM `User` u
        WHERE u.user_type = 'MANUFACTURER'
          AND u.user_id NOT IN (
              SELECT DISTINCT pb.manufacturer_id
              FROM ProductBatch pb
              JOIN ProductionConsumption pc ON pb.lot_number = pc.product_batch
              JOIN IngredientBatch ib ON pc.ingredient_lot = ib.lot_number
              WHERE ib.supplier_id = 21
          )
        ORDER BY u.first_name, u.last_name
    """, fetch=True)
    
    if result:
        print_table(['First Name', 'Last Name'], result)
    else:
        print("\nAll manufacturers have been supplied by this supplier.")