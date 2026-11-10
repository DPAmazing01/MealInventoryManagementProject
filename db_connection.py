"""
Database Connection Module
"""

import mysql.connector
from mysql.connector import Error


# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'database': 'inventory_management',
    'user': 'root',
    'password': '',  # Change this to your MySQL password
    'port': 3306
}


def get_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def close_connection(connection):
    """Close database connection"""
    if connection and connection.is_connected():
        connection.close()


def execute_query(query, params=None, fetch=False):
    """Execute a query and return results if fetch=True"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            result = cursor.fetchall()
            cursor.close()
            close_connection(connection)
            return result
        else:
            last_id = cursor.lastrowid   # <-- GRAB THE INSERT ID
            connection.commit()
            cursor.close()
            close_connection(connection)
            # Return last inserted ID if available, otherwise True
            return last_id if last_id != 0 else True
    except Error as e:
        print(f"\nDatabase Error: {e}")
        if connection:
            connection.rollback()
            close_connection(connection)
        return None


def call_procedure(proc_name, params=None):
    """Call a stored procedure"""
    connection = get_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.callproc(proc_name, params or ())
        
        # Fetch results if any
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        
        connection.commit()
        cursor.close()
        close_connection(connection)
        return results
    except Error as e:
        print(f"\nProcedure Error: {e}")
        if connection:
            connection.rollback()
            close_connection(connection)
        return None