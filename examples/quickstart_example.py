"""
ArcadeDB Python Driver - Complete Quick Start Example

This example demonstrates all the code from the README.md Quick Start section.
Run this file to see a complete working example of the ArcadeDB Python driver.

Requirements:
- ArcadeDB running on localhost:2480
- Default credentials (root/playwithdata)
"""

from arcadedb_python import DatabaseDao, SyncClient


def main():
    print("=" * 70)
    print("ArcadeDB Python Driver - Quick Start Example")
    print("=" * 70)
    
    # ========================================================================
    # Step 1: Create a client connection
    # ========================================================================
    print("\n[1] Creating client connection...")
    client = SyncClient(
        host="localhost",
        port=2480,
        username="root",
        password="playwithdata"
    )
    print("    [OK] Client connected")
    
    # ========================================================================
    # Step 2: Connect to database (or create it)
    # ========================================================================
    print("\n[2] Connecting to database...")
    database_name = "quickstart_example"
    
    if not DatabaseDao.exists(client, database_name):
        print(f"    Creating database '{database_name}'...")
        db = DatabaseDao.create(client, database_name)
        print(f"    [OK] Database '{database_name}' created")
    else:
        print(f"    Database '{database_name}' already exists")
        db = DatabaseDao(client, database_name)
        print(f"    [OK] Connected to database '{database_name}'")
    
    # ========================================================================
    # Step 3: Create schema (DDL requires is_command=True)
    # ========================================================================
    print("\n[3] Creating schema...")
    db.query("sql", "CREATE VERTEX TYPE Person IF NOT EXISTS", is_command=True)
    print("    [OK] Created vertex type 'Person'")
    
    # ========================================================================
    # Step 4: Insert data (DML requires is_command=True)
    # ========================================================================
    print("\n[4] Inserting data...")
    db.query("sql", "INSERT INTO Person SET name = 'John', age = 30", is_command=True)
    db.query("sql", "INSERT INTO Person SET name = 'Jane', age = 25", is_command=True)
    db.query("sql", "INSERT INTO Person SET name = 'Bob', age = 35", is_command=True)
    print("    [OK] Inserted 3 people")
    
    # ========================================================================
    # Step 5: Query data
    # ========================================================================
    print("\n[5] Querying data...")
    result = db.query("sql", "SELECT FROM Person LIMIT 10")
    print(f"    [OK] Found {len(result)} people:")
    for person in result:
        print(f"      - {person['name']}, age {person['age']}")
    
    # ========================================================================
    # Step 6: Graph traversal
    # ========================================================================
    print("\n[6] Graph traversal with MATCH...")
    result = db.query("sql", """
        MATCH {type: Person, as: person} 
        RETURN person.name, person.age
        ORDER BY person.age
    """)
    print(f"    [OK] MATCH query found {len(result)} people:")
    for row in result:
        print(f"      - {row['person.name']}, age {row['person.age']}")
    
    # ========================================================================
    # Advanced Usage: Different Data Models
    # ========================================================================
    print("\n" + "=" * 70)
    print("Advanced Usage - Different Data Models")
    print("=" * 70)
    
    # Document operations (documents are schema-flexible records; they cannot be edge endpoints)
    # Vertices are documents with added capability: they can be connected by edges
    print("\n[7] Document operations...")
    db.query("sql", "CREATE DOCUMENT TYPE Product IF NOT EXISTS", is_command=True)
    db.query("sql", """
        INSERT INTO Product CONTENT {
            "name": "Laptop",
            "price": 999.99,
            "specs": {
                "cpu": "Intel i7",
                "ram": "16GB"
            }
        }
    """, is_command=True)
    products = db.query("sql", "SELECT FROM Product")
    print(f"    [OK] Created document type 'Product' and inserted {len(products)} product(s)")

    # Graph operations (edges connect vertex types only - both ends must be VERTEX TYPE)
    print("\n[8] Graph operations...")
    db.query("sql", "CREATE VERTEX TYPE Customer IF NOT EXISTS", is_command=True)
    db.query("sql", "CREATE VERTEX TYPE ItemType IF NOT EXISTS", is_command=True)
    db.query("sql", "CREATE EDGE TYPE Purchased IF NOT EXISTS", is_command=True)
    db.query("sql", "INSERT INTO Customer SET name = 'Alice'", is_command=True)
    db.query("sql", "INSERT INTO ItemType SET name = 'Laptop', price = 999.99", is_command=True)
    print("    [OK] Created vertex types Customer and ItemType, and edge type Purchased")
    db.query("sql", """
        CREATE EDGE Purchased
        FROM (SELECT FROM Customer WHERE name = 'Alice')
        TO (SELECT FROM ItemType WHERE name = 'Laptop')
        SET date = sysdate(), amount = 999.99
    """, is_command=True)
    print("    [OK] Created purchase edge from Alice to Laptop")
    traversal = db.query("sql", "SELECT expand(out('Purchased')) FROM Customer WHERE name = 'Alice'")
    print(f"    [OK] Traversal found {len(traversal)} purchased item(s)")
    
    # Key-Value operations
    print("\n[9] Key-Value operations...")
    db.query("sql", "CREATE DOCUMENT TYPE Settings IF NOT EXISTS", is_command=True)
    db.query("sql", "INSERT INTO Settings SET key = 'theme', value = 'dark'", is_command=True)
    db.query("sql", "INSERT INTO Settings SET key = 'language', value = 'en'", is_command=True)
    
    settings = db.query("sql", "SELECT FROM Settings")
    print(f"    [OK] Stored {len(settings)} settings:")
    for setting in settings:
        print(f"      - {setting['key']}: {setting['value']}")
    
    # Time-Series operations
    print("\n[10] Time-Series operations...")
    db.query("sql", "CREATE VERTEX TYPE Sensor IF NOT EXISTS", is_command=True)
    db.query("sql", """
        INSERT INTO Sensor SET 
        sensor_id = 'temp_01', 
        timestamp = sysdate(), 
        temperature = 23.5
    """, is_command=True)
    db.query("sql", """
        INSERT INTO Sensor SET 
        sensor_id = 'temp_01', 
        timestamp = sysdate(), 
        temperature = 24.1
    """, is_command=True)
    
    sensors = db.query("sql", "SELECT FROM Sensor WHERE sensor_id = 'temp_01'")
    print(f"    [OK] Recorded {len(sensors)} sensor readings:")
    for reading in sensors:
        print(f"      - Sensor {reading['sensor_id']}: {reading['temperature']}°C")
    
    # Vector Search
    print("\n[11] Vector operations...")
    db.query("sql", "CREATE VERTEX TYPE DocRecord IF NOT EXISTS", is_command=True)
    db.query("sql", "CREATE PROPERTY DocRecord.embedding IF NOT EXISTS ARRAY_OF_FLOATS", is_command=True)
    db.create_vector_index("DocRecord", "embedding", dimensions=4)
    db.query("sql", """
        INSERT INTO DocRecord CONTENT {
            "title": "AI Research Paper",
            "embedding": [0.1, 0.2, 0.3, 0.4],
            "content": "Full document text..."
        }
    """, is_command=True)
    db.query("sql", """
        INSERT INTO DocRecord CONTENT {
            "title": "Machine Learning Guide",
            "embedding": [0.9, 0.8, 0.7, 0.6],
            "content": "Intro to ML..."
        }
    """, is_command=True)
    print("    [OK] Created DocRecord type with vector index (4 dimensions)")

    results = db.vector_search(
        type_name="DocRecord",
        embedding_field="embedding",
        query_embedding=[0.1, 0.2, 0.3, 0.4],
        top_k=2
    )
    print(f"    [OK] Vector search returned {len(results)} result(s):")
    for doc in results:
        print(f"      - {doc['title']}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"[OK] Database: {database_name}")
    print(f"[OK] Types created: Person, Product (document), Customer, ItemType, Settings, Sensor, DocRecord (vector)")
    print(f"[OK] Edges created: Purchased (Customer -> ItemType)")
    print(f"[OK] All operations completed successfully!")
    print("\n" + "=" * 70)
    
    # Optional: Cleanup
    cleanup = input("\nClean up test data? (y/N): ").strip().lower()
    if cleanup == 'y':
        print("\nCleaning up...")
        # Drop DocRecord with its vector index first (UNSAFE drops the type and all indexes)
        try:
            db.query("sql", "DROP TYPE DocRecord UNSAFE", is_command=True)
            print("    [OK] Dropped DocRecord (with vector index)")
        except Exception:
            pass
        types_to_clean = ["Person", "Product", "Purchased", "Customer", "ItemType", "Settings", "Sensor"]
        for type_name in types_to_clean:
            try:
                result = db.query("sql", f"DELETE FROM {type_name}", is_command=True)
                count = result[0]['count'] if result and len(result) > 0 and 'count' in result[0] else 0
                if count > 0:
                    print(f"    [OK] Deleted {count} records from {type_name}")
            except Exception:
                pass
        print("    [OK] Cleanup complete")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

