#!/usr/bin/env python3
"""
Enhanced ArcadeDB Python Driver Demo

This script demonstrates the new features added to address critical issues
identified in the LlamaIndex integration, including:

1. Typed exceptions for better error handling
2. Bulk operations for improved performance
3. Vector operations for similarity search
4. Enhanced transaction management
5. Better query parsing with fallback mechanisms

Usage:
    python enhanced_features_demo.py
"""

import json
import logging
from typing import List, Dict, Any

from arcadedb_python import (
    DatabaseDao,
    SyncClient,
    ArcadeDBException,
    QueryParsingException,
    TransactionException,
    BulkOperationException,
    VectorOperationException,
    ValidationException
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def demo_exception_handling():
    """Demonstrate the new typed exception system."""
    print("\n" + "="*50)
    print("DEMO: Enhanced Exception Handling")
    print("="*50)
    
    try:
        # Create a client (this will fail without a running ArcadeDB instance)
        client = SyncClient("localhost", "2480", username="root", password="test")
        db = DatabaseDao(client, "demo_db")
        
        # This would normally raise a generic exception
        # Now it raises a specific ConnectionException
        result = db.query("sql", "SELECT 1")
        
    except ArcadeDBException as e:
        print(f"✓ Caught specific exception: {type(e).__name__}")
        print(f"  Message: {e.message}")
        print(f"  Java Error Code: {e.java_error_code}")
        print(f"  Detail: {e.detail}")
        
        # Check for specific exception types
        if isinstance(e, QueryParsingException):
            print(f"  Failed Query: {e.query}")
        elif isinstance(e, TransactionException):
            print(f"  Session ID: {e.session_id}")
            print(f"  Is Idempotent Error: {e.is_idempotent_error}")
        elif isinstance(e, BulkOperationException):
            print(f"  Failed Records: {e.failed_records}/{e.total_records}")
    
    except Exception as e:
        print(f"✗ Caught generic exception: {e}")


def demo_bulk_operations(db: DatabaseDao):
    """Demonstrate bulk operations functionality."""
    print("\n" + "="*50)
    print("DEMO: Bulk Operations")
    print("="*50)
    
    try:
        # Sample data for bulk operations
        sample_records = [
            {"name": "John Doe", "age": 30, "city": "New York", "email": "john@example.com"},
            {"name": "Jane Smith", "age": 25, "city": "Los Angeles", "email": "jane@example.com"},
            {"name": "Bob Johnson", "age": 35, "city": "Chicago", "email": "bob@example.com"},
            {"name": "Alice Brown", "age": 28, "city": "Houston", "email": "alice@example.com"},
            {"name": "Charlie Wilson", "age": 32, "city": "Phoenix", "email": "charlie@example.com"}
        ]
        
        # 1. Bulk Insert
        print("\n1. Bulk Insert Demo:")
        try:
            inserted_count = db.bulk_insert("Person", sample_records, batch_size=2)
            print(f"✓ Successfully inserted {inserted_count} records")
        except BulkOperationException as e:
            print(f"✗ Bulk insert failed: {e}")
            print(f"  Failed: {e.failed_records}/{e.total_records} records")
        
        # 2. Bulk Upsert
        print("\n2. Bulk Upsert Demo:")
        upsert_records = [
            {"email": "john@example.com", "name": "John Doe Updated", "age": 31},
            {"email": "new@example.com", "name": "New Person", "age": 40}
        ]
        try:
            upserted_count = db.bulk_upsert("Person", upsert_records, "email")
            print(f"✓ Successfully upserted {upserted_count} records")
        except BulkOperationException as e:
            print(f"✗ Bulk upsert failed: {e}")
        
        # 3. Batch Query Execution
        print("\n3. Batch Query Execution Demo:")
        queries = [
            "SELECT COUNT(*) as total FROM Person",
            "SELECT name FROM Person WHERE age > 30",
            "SELECT city, COUNT(*) as count FROM Person GROUP BY city"
        ]
        try:
            results = db.execute_batch(queries)
            print(f"✓ Executed {len(queries)} queries successfully")
            for i, result in enumerate(results):
                print(f"  Query {i+1} result: {result}")
        except Exception as e:
            print(f"✗ Batch execution failed: {e}")
        
        # 4. Transaction Execution
        print("\n4. Transaction Execution Demo:")
        transaction_queries = [
            "INSERT INTO Person SET name = 'Transaction Test', age = 25",
            "UPDATE Person SET age = age + 1 WHERE name = 'Transaction Test'"
        ]
        try:
            results = db.execute_transaction(transaction_queries)
            print(f"✓ Transaction completed successfully")
        except TransactionException as e:
            print(f"✗ Transaction failed: {e}")
            print(f"  Session ID: {e.session_id}")
        
        # 5. Safe Bulk Delete
        print("\n5. Safe Bulk Delete Demo:")
        try:
            # Delete records with specific conditions
            conditions = ["age < 25", "name LIKE '%Test%'"]
            deleted_count = db.bulk_delete("Person", conditions, safe_mode=True)
            print(f"✓ Safely deleted approximately {deleted_count} records")
        except ValidationException as e:
            print(f"✗ Safe delete validation failed: {e}")
        except BulkOperationException as e:
            print(f"✗ Bulk delete failed: {e}")
    
    except Exception as e:
        print(f"✗ Bulk operations demo failed: {e}")


def demo_vector_operations(db: DatabaseDao):
    """Demonstrate vector operations functionality."""
    print("\n" + "="*50)
    print("DEMO: Vector Operations")
    print("="*50)
    
    try:
        # Sample documents with embeddings
        documents = [
            {
                "title": "Machine Learning Basics",
                "content": "Introduction to machine learning algorithms",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
            },
            {
                "title": "Deep Learning Guide", 
                "content": "Neural networks and deep learning",
                "embedding": [0.2, 0.3, 0.4, 0.5, 0.6]
            },
            {
                "title": "Data Science Overview",
                "content": "Data analysis and visualization",
                "embedding": [0.15, 0.25, 0.35, 0.45, 0.55]
            }
        ]
        
        # 1. Insert documents with embeddings
        print("\n1. Inserting documents with embeddings:")
        try:
            inserted = db.bulk_insert("Document", documents)
            print(f"✓ Inserted {inserted} documents with embeddings")
        except Exception as e:
            print(f"✗ Failed to insert documents: {e}")
        
        # 2. Create vector index
        print("\n2. Creating vector index:")
        try:
            index_created = db.create_vector_index("Document", "embedding", 5, "HNSW")
            if index_created:
                print("✓ Vector index created successfully")
            else:
                print("✗ Vector index creation failed")
        except VectorOperationException as e:
            print(f"✗ Vector index creation failed: {e}")
            print(f"  Dimensions: {e.dimensions}")
        
        # 3. Vector similarity search
        print("\n3. Vector similarity search:")
        query_embedding = [0.12, 0.22, 0.32, 0.42, 0.52]  # Similar to first document
        try:
            similar_docs = db.vector_search(
                "Document", 
                "embedding", 
                query_embedding, 
                top_k=3,
                where_clause="title IS NOT NULL"
            )
            print(f"✓ Found {len(similar_docs)} similar documents:")
            for doc in similar_docs:
                title = doc.get('title', 'Unknown')
                score = doc.get('similarity_score', 0.0)
                print(f"  - {title} (similarity: {score:.3f})")
        except VectorOperationException as e:
            print(f"✗ Vector search failed: {e}")
        
        # 4. Calculate specific similarity
        print("\n4. Calculate vector similarity:")
        try:
            # Assuming we have a document with ID #1:1
            similarity = db.get_vector_similarity(
                "Document", 
                "embedding", 
                "#1:1", 
                query_embedding
            )
            print(f"✓ Similarity to document #1:1: {similarity:.3f}")
        except VectorOperationException as e:
            print(f"✗ Similarity calculation failed: {e}")
        
        # 5. Batch vector search
        print("\n5. Batch vector search:")
        batch_searches = [
            {
                "type_name": "Document",
                "embedding_field": "embedding",
                "query_embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "top_k": 2
            },
            {
                "type_name": "Document", 
                "embedding_field": "embedding",
                "query_embedding": [0.2, 0.3, 0.4, 0.5, 0.6],
                "top_k": 2
            }
        ]
        try:
            batch_results = db.batch_vector_search(batch_searches)
            print(f"✓ Completed {len(batch_results)} vector searches")
            for i, results in enumerate(batch_results):
                print(f"  Search {i+1}: {len(results)} results")
        except VectorOperationException as e:
            print(f"✗ Batch vector search failed: {e}")
    
    except Exception as e:
        print(f"✗ Vector operations demo failed: {e}")


def demo_enhanced_query_parsing(db: DatabaseDao):
    """Demonstrate enhanced query parsing with fallback mechanisms."""
    print("\n" + "="*50)
    print("DEMO: Enhanced Query Parsing")
    print("="*50)
    
    try:
        # 1. Multi-type record retrieval
        print("\n1. Multi-type record retrieval:")
        try:
            # This handles UNION queries with fallback to individual queries
            records = db.get_records(
                ["Person", "Document"], 
                where_clause="name IS NOT NULL OR title IS NOT NULL",
                limit=10
            )
            print(f"✓ Retrieved {len(records)} records from multiple types")
        except QueryParsingException as e:
            print(f"✗ Multi-type query failed: {e}")
            print(f"  Failed query: {e.query}")
        
        # 2. Graph triplet retrieval
        print("\n2. Graph triplet retrieval:")
        try:
            # This handles MATCH queries with fallback to edge traversal
            triplets = db.get_triplets(
                subject_types=["Person"],
                relation_types=["KNOWS", "WORKS_WITH"],
                object_types=["Person"],
                limit=5
            )
            print(f"✓ Retrieved {len(triplets)} graph triplets")
            for triplet in triplets[:2]:  # Show first 2
                subject = triplet.get('subject', {}).get('name', 'Unknown')
                relation = triplet.get('relation', {}).get('@class', 'Unknown')
                obj = triplet.get('object', {}).get('name', 'Unknown')
                print(f"  {subject} --[{relation}]--> {obj}")
        except QueryParsingException as e:
            print(f"✗ Triplet query failed: {e}")
        
        # 3. Safe delete all with batching
        print("\n3. Safe delete all with batching:")
        try:
            # This handles non-idempotent DELETE operations
            deleted_count = db.safe_delete_all("TempData", batch_size=100)
            print(f"✓ Safely deleted {deleted_count} records using batching")
        except TransactionException as e:
            print(f"✗ Safe delete failed: {e}")
            if e.is_idempotent_error:
                print("  This was an idempotent error - automatic retry attempted")
        
        # 4. Query with automatic retry
        print("\n4. Query with automatic retry on idempotent errors:")
        try:
            # This automatically retries non-idempotent queries as commands
            result = db.query(
                "sql", 
                "DELETE FROM Person WHERE age > 100",
                retry_on_idempotent_error=True
            )
            print("✓ Query executed successfully (with automatic retry if needed)")
        except TransactionException as e:
            print(f"✗ Query failed even with retry: {e}")
    
    except Exception as e:
        print(f"✗ Enhanced query parsing demo failed: {e}")


def demo_transaction_management(db: DatabaseDao):
    """Demonstrate enhanced transaction management."""
    print("\n" + "="*50)
    print("DEMO: Enhanced Transaction Management")
    print("="*50)
    
    try:
        # 1. Manual transaction management
        print("\n1. Manual transaction management:")
        session_id = None
        try:
            session_id = db.begin_transaction()
            print(f"✓ Started transaction: {session_id}")
            
            # Execute some operations in the transaction
            db.query("sql", "INSERT INTO Person SET name = 'Transaction User'", session_id=session_id)
            db.query("sql", "UPDATE Person SET age = 30 WHERE name = 'Transaction User'", session_id=session_id)
            
            # Get transaction status
            status = db.get_transaction_status(session_id)
            print(f"✓ Transaction status: {status.get('status', 'unknown')}")
            
            # Commit the transaction
            db.commit_transaction(session_id)
            print("✓ Transaction committed successfully")
            
        except Exception as e:
            if session_id:
                db.rollback_transaction(session_id)
                print(f"✗ Transaction rolled back due to error: {e}")
            else:
                print(f"✗ Transaction failed to start: {e}")
        
        # 2. Safe bulk operation with retry
        print("\n2. Safe bulk operation with retry:")
        def sample_bulk_operation():
            # Simulate a bulk operation that might fail
            import random
            if random.random() < 0.3:  # 30% chance of failure
                raise BulkOperationException("Simulated failure", failed_records=1, total_records=10)
            return 10
        
        try:
            result = db.safe_bulk_operation(
                sample_bulk_operation,
                max_retries=3,
                retry_delay=0.1
            )
            print(f"✓ Bulk operation completed successfully: {result} records processed")
        except Exception as e:
            print(f"✗ Bulk operation failed after retries: {e}")
        
        # 3. Automatic transaction execution
        print("\n3. Automatic transaction execution:")
        transaction_queries = [
            "CREATE VERTEX Person SET name = 'Auto Transaction User', age = 25",
            "CREATE EDGE Knows FROM (SELECT FROM Person WHERE name = 'Auto Transaction User') TO (SELECT FROM Person WHERE name = 'Transaction User')"
        ]
        try:
            results = db.execute_transaction(transaction_queries)
            print(f"✓ Automatic transaction completed: {len(results)} operations")
        except TransactionException as e:
            print(f"✗ Automatic transaction failed: {e}")
    
    except Exception as e:
        print(f"✗ Transaction management demo failed: {e}")


def main():
    """Main demo function."""
    print("ArcadeDB Python Driver - Enhanced Features Demo")
    print("=" * 60)
    
    # Demo exception handling (works without database connection)
    demo_exception_handling()
    
    # For the following demos, we would need a running ArcadeDB instance
    print("\n" + "!"*60)
    print("NOTE: The following demos require a running ArcadeDB instance")
    print("      at localhost:2480 with username 'root' and password 'test'")
    print("!"*60)
    
    try:
        # Try to connect to ArcadeDB
        client = SyncClient("localhost", "2480", username="root", password="test")
        
        # Create or connect to demo database
        try:
            db = DatabaseDao(client, "enhanced_demo")
        except Exception:
            # Database might not exist, try to create it
            DatabaseDao.create(client, "enhanced_demo")
            db = DatabaseDao(client, "enhanced_demo")
        
        print("\n✓ Connected to ArcadeDB successfully!")
        
        # Run all demos
        demo_bulk_operations(db)
        demo_vector_operations(db)
        demo_enhanced_query_parsing(db)
        demo_transaction_management(db)
        
        print("\n" + "="*60)
        print("✓ All demos completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Could not connect to ArcadeDB: {e}")
        print("Please ensure ArcadeDB is running and accessible.")
        print("\nTo run ArcadeDB with Docker:")
        print("docker run -d --name arcadedb -p 2480:2480 -p 2424:2424 \\")
        print("  -e JAVA_OPTS='-Darcadedb.server.rootPassword=test' \\")
        print("  arcadedata/arcadedb:latest")


if __name__ == "__main__":
    main()
