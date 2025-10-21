"""
Test Cypher and Gremlin examples from README.md

This script tests the simple Cypher and Gremlin examples to ensure they work correctly.
"""

from arcadedb_python import DatabaseDao, SyncClient


def test_cypher():
    """Test Cypher query language examples"""
    print("\n" + "=" * 70)
    print("Testing Cypher Examples")
    print("=" * 70)
    
    # Connect
    client = SyncClient("localhost", 2480, username="root", password="playwithdata")
    
    # Create or connect to database
    db_name = "cypher_test"
    if DatabaseDao.exists(client, db_name):
        DatabaseDao.delete(client, db_name)
    
    db = DatabaseDao.create(client, db_name)
    print("[OK] Created database:", db_name)
    
    # Create nodes
    db.query("cypher", "CREATE (p:Person {name: 'John', age: 30})", is_command=True)
    db.query("cypher", "CREATE (p:Person {name: 'Jane', age: 25})", is_command=True)
    print("[OK] Created Person nodes")
    
    # Create relationship
    db.query("cypher", """
        MATCH (a:Person {name: 'John'}), (b:Person {name: 'Jane'})
        CREATE (a)-[:KNOWS]->(b)
    """, is_command=True)
    print("[OK] Created KNOWS relationship")
    
    # Query with Cypher
    result = db.query("cypher", "MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age")
    print(f"[OK] Query returned {len(result)} results:")
    for row in result:
        print(f"    - {row}")
    
    # Cleanup
    DatabaseDao.delete(client, db_name)
    print("[OK] Cleaned up database")
    

def test_gremlin():
    """Test Gremlin query language examples"""
    print("\n" + "=" * 70)
    print("Testing Gremlin Examples")
    print("=" * 70)
    
    # Connect
    client = SyncClient("localhost", 2480, username="root", password="playwithdata")
    
    # Create or connect to database
    db_name = "gremlin_test"
    if DatabaseDao.exists(client, db_name):
        DatabaseDao.delete(client, db_name)
    
    db = DatabaseDao.create(client, db_name)
    print("[OK] Created database:", db_name)
    
    # Need to create vertex type first for Gremlin
    db.query("sql", "CREATE VERTEX TYPE Person IF NOT EXISTS", is_command=True)
    print("[OK] Created Person vertex type")
    
    # Add vertices
    db.query("gremlin", "g.addV('Person').property('name', 'John').property('age', 30)", is_command=True)
    db.query("gremlin", "g.addV('Person').property('name', 'Jane').property('age', 25)", is_command=True)
    print("[OK] Added Person vertices")
    
    # Query with Gremlin
    result = db.query("gremlin", "g.V().hasLabel('Person').values('name')")
    print(f"[OK] Query returned {len(result)} names:")
    for name in result:
        print(f"    - {name}")
    
    # Traversal with filter
    result = db.query("gremlin", "g.V().hasLabel('Person').has('age', gt(20)).valueMap()")
    print(f"[OK] Filtered query returned {len(result)} results:")
    for row in result:
        print(f"    - {row}")
    
    # Cleanup
    DatabaseDao.delete(client, db_name)
    print("[OK] Cleaned up database")


def main():
    print("\n" + "=" * 70)
    print("README.md Query Language Examples Test")
    print("=" * 70)
    
    try:
        test_cypher()
        print("\n[OK] Cypher tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Cypher test failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_gremlin()
        print("\n[OK] Gremlin tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Gremlin test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()

