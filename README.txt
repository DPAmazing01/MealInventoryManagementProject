(Project was worked on from September-November 2025 in a team of 4, where I helped with setting up the SQL schema and predefined queries in the application along with implementing the Supplier and Manufacturer roles in the system)

Project is a meal inventory management system where the data for the system is defined in SQL, and a Python UI-interface is used to interact with the SQL-defined data (Data defined in Sample Data.sql was provided by class professor) - Refer to "Meal Inventory Management System Requirements" PDF for in-depth details about the system 

Meal Inventory Management Program Setup & Execution (Requires having a MySQL account)

* NOTE: If needed, use these commands to setup a virtual environment for installing the program 
dependencies in the project directory -
"python3 -m venv tfenv
source tfenv/bin/activate"

1. Run "pip install -r requirements.txt"
2. In the db_connections.py file, update the "password" field of DB_CONFIG to the password of your own MySQL account and save the modified file
3. Run "python3 main.py" to execute the program
