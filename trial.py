import sqlite3

# Connect to fines.db
conn = sqlite3.connect('fines.db')
cursor = conn.cursor()

# Get the list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

if tables:
    print("✅ Tables in fines.db:", tables)
else:
    print("❌ No tables found! You need to create the 'fines' table.")

conn.close()
