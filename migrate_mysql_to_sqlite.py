import sqlite3
import mysql.connector
import getpass

# Prompt user for MySQL credentials
mysql_user = input("Enter MySQL username: ")
mysql_password = getpass.getpass("Enter MySQL password: ")
mysql_host = input("Enter MySQL host (default: localhost): ") or "localhost"
mysql_database = input("Enter MySQL database name: ")

# MySQL connection configuration
mysql_config = {
    'user': mysql_user,
    'password': mysql_password,
    'host': mysql_host,
    'database': mysql_database
}

# SQLite database file
sqlite_file = 'tacacsgui.db'

# Connect to MySQL
mysql_conn = mysql.connector.connect(**mysql_config)
mysql_cursor = mysql_conn.cursor()

# Connect to SQLite
sqlite_conn = sqlite3.connect(sqlite_file)
sqlite_cursor = sqlite_conn.cursor()

# Define tables to migrate
tables = ['auth_user', 'tac_plus_system']

for table in tables:
    # Fetch data from MySQL
    mysql_cursor.execute(f"SELECT * FROM {table}")
    rows = mysql_cursor.fetchall()

    # Get column names
    column_names = [desc[0] for desc in mysql_cursor.description]

    # Insert data into SQLite
    placeholders = ', '.join(['?'] * len(column_names))
    sqlite_cursor.executemany(
        f"INSERT INTO {table} ({', '.join(column_names)}) VALUES ({placeholders})",
        rows
    )

# Commit and close connections
sqlite_conn.commit()
sqlite_conn.close()
mysql_cursor.close()
mysql_conn.close()

print("Migration completed successfully.")
