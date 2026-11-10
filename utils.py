"""
Utility Functions
"""

import os
from datetime import datetime, timedelta


def print_header(title):
    """Print a formatted header"""
    print("=" * 60)
    print(f" {title}")
    print("=" * 60)

def login(expected_role):
    """Login with username and password authentication for a specific role"""
    from db_connection import execute_query  # Import here to avoid circular dependency
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    # Query user by username
    user = execute_query("""
        SELECT user_id, username, first_name, last_name, user_type, password_hash
        FROM `User`
        WHERE username = %s AND user_type = %s
    """, (username, expected_role), fetch=True)
    
    if not user:
        print("\nInvalid username or password!")
        return None
    
    user_data = user[0]
    
    # Verify password (simple comparison - sample data uses 'hash' as password)
    if user_data['password_hash'] != password:
        print("\nInvalid username or password!")
        return None
    
    return user_data['user_id']

def print_table(headers, rows):
    """Print data in table format"""
    if not rows:
        print("\nNo data found.")
        return
    
    # Calculate column widths
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row.values()):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    # Print header
    print()
    header_row = " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
    print(header_row)
    print("-" * len(header_row))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row.values()))
        print(row_str)
    print()


def get_date_input(prompt, allow_empty=False):
    """Get a valid date input from user"""
    while True:
        date_str = input(prompt).strip()
        if allow_empty and not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")


def get_number_input(prompt, allow_decimal=False, allow_empty=False):
    """Get a valid number input from user"""
    while True:
        value = input(prompt).strip()
        if allow_empty and not value:
            return None
        try:
            return float(value) if allow_decimal else int(value)
        except ValueError:
            print(f"Invalid {'number' if allow_decimal else 'integer'}. Try again.")


def confirm_action(prompt="Are you sure? (y/n): "):
    """Get confirmation from user"""
    response = input(prompt).strip().lower()
    return response in ['y', 'yes']