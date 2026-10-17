from src.database import get_connection, DB_PATH

print("Database location:", DB_PATH)

connection = get_connection()

try:
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packing_lists (
            packing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL UNIQUE,
            packing_status TEXT NOT NULL DEFAULT 'Pending'
                CHECK (
                    packing_status IN (
                        'Pending',
                        'Packed',
                        'Dispatched'
                    )
                ),
            packing_date TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (invoice_id)
                REFERENCES invoices(invoice_id)
        )
    """)

    connection.commit()

    print("\nPacking list table created successfully!")

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """)

    print("\nDatabase tables:")

    for table in cursor.fetchall():
        print("-", table[0])

except Exception as error:
    print("Error:", error)

finally:
    connection.close()