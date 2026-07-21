import sqlite3

conn = sqlite3.connect("shipments.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM shipments")
count = cursor.fetchone()[0]

print("Total shipments in DB:", count)

cursor.execute("SELECT * FROM shipments LIMIT 5")
rows = cursor.fetchall()

for r in rows:
    print(r)

conn.close()