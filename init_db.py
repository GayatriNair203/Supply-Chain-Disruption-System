from models.shipment_db import init_db, seed_data

init_db()
seed_data()

print("Database initialized with 100 shipments")