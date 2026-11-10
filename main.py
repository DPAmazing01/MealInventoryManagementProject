"""
Inventory Management System - Main Entry Point
"""

import sys
from db_connection import get_connection, close_connection
from manufacturer import manufacturer_menu
from supplier import supplier_menu
from viewer import viewer_menu
from queries import queries_menu
from utils import print_header, login


def select_roles():
    """Select role and login"""
    print("Login")
    print("Select role:")
    print("[1] Manufacturer")
    print("[2] Supplier")
    print("[3] General (Viewer)")
    print("[4] View Queries")
    print("[0] Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == '0':
        return None, None
    elif choice == '1':
        print("\n=== Manufacturer Login ===")
        user_id = login('MANUFACTURER')
        print("\n")
        return user_id, 'MANUFACTURER' if user_id else (None, 'RETRY')
    elif choice == '2':
        print("\n=== Supplier Login ===")
        user_id = login('SUPPLIER')
        print("\n")
        return user_id, 'SUPPLIER' if user_id else (None, 'RETRY')
    elif choice == '3':
        print("\n=== Viewer Login ===")
        user_id = login('VIEWER')
        print("\n")
        return user_id, 'VIEWER' if user_id else (None, 'RETRY')
    elif choice == '4':
        print("\n")
        return 'QUERY', 'QUERY'
    else:
        print("Invalid choice!")
        return None, 'RETRY'


def main():
    """Main application loop"""
    print_header("CSC540 Project 1 - Inventory Management System")
    
    # Test database connection
    conn = get_connection()
    if not conn:
        print("Failed to connect to database. Please check your connection settings.")
        sys.exit(1)
    close_connection(conn)
    
    while True:
        user_id, role = select_roles()

        if user_id is None and role is None:
            print("\nThank you for using the Inventory Management System!")
            break
        
        if role == 'RETRY':
            continue
        if role == 'MANUFACTURER':
            manufacturer_menu(user_id)
        elif role == 'SUPPLIER':
            supplier_menu(user_id)
        elif role == 'VIEWER':
            viewer_menu(user_id)
        elif role == 'QUERY':
            queries_menu()
        
        print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting application...")
        sys.exit(0)