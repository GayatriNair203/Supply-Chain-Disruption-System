import sqlite3
import random

DB_NAME = "shipments.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id TEXT PRIMARY KEY,
        origin TEXT,
        destination TEXT,
        shipment_type TEXT,
        priority TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


def seed_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cities = [
        "Houston", "Dallas", "Atlanta", "Chicago", "Los Angeles",
        "Seattle", "Miami", "New York", "Boston", "Denver",
        "Phoenix", "San Francisco", "Orlando", "Charlotte", "Memphis"
    ]

    shipment_types = [
        "Pharmaceuticals",
        "Medical Equipment",
        "Electronics",
        "Automotive Parts",
        "Perishable Food",
        "Textiles",
        "Industrial Machinery",
        "Chemicals",
        "Retail Goods",
        "Aerospace Components"
    ]

    data = []

    for i in range(1, 101):
        shipment_id = f"SHP{i:03d}"
        origin = random.choice(cities)
        destination = random.choice([c for c in cities if c != origin])
        shipment_type = random.choice(shipment_types)
        priority = random.choice(["Low", "Medium", "High"])
        status = random.choices(
            ["Scheduled", "In Transit", "Delayed"],
            weights=[0.5, 0.35, 0.15]
        )[0]

        data.append((shipment_id, origin, destination, shipment_type, priority, status))

    cursor.executemany("""
    INSERT OR IGNORE INTO shipments VALUES (?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()


def get_shipment(origin, destination, shipment_type):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM shipments
    WHERE origin = ? AND destination = ? AND shipment_type = ?
    """, (origin, destination, shipment_type))

    result = cursor.fetchone()

    conn.close()
    return result
def get_shipment_by_id(shipment_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM shipments
        WHERE shipment_id = ?
    """, (shipment_id,))

    shipment = cursor.fetchone()

    conn.close()

    return shipment