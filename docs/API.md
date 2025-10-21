# ArcadeDB Python Driver - API Documentation

## Table of Contents

1. [Client](#client)
2. [DatabaseDao](#databasedao)
3. [Exceptions](#exceptions)
4. [Configuration](#configuration)

---

## Client

### SyncClient

The `SyncClient` class handles HTTP connections to ArcadeDB.

#### Constructor

```python
SyncClient(host: str, port: int, username: str = None, password: str = None, protocol: str = "http")
```

**Parameters:**
- `host` (str): ArcadeDB server hostname
- `port` (int): ArcadeDB server port (default: 2480)
- `username` (str, optional): Database username
- `password` (str, optional): Database password
- `protocol` (str, optional): Protocol to use ("http" or "https", default: "http")

**Example:**
```python
from arcadedb_python import SyncClient

client = SyncClient(
    host="localhost",
    port=2480,
    username="root",
    password="playwithdata"
)
```

---

## DatabaseDao

The `DatabaseDao` class is the main interface for database operations.

### Static Methods

#### `exists(client, name)`

Check if a database exists.

```python
DatabaseDao.exists(client: Client, name: str) -> bool
```

**Parameters:**
- `client`: SyncClient instance
- `name`: Database name

**Returns:** `bool` - True if database exists

**Example:**
```python
if DatabaseDao.exists(client, "mydb"):
    print("Database exists")
```

#### `create(client, name)`

Create a new database.

```python
DatabaseDao.create(client: Client, name: str) -> DatabaseDao
```

**Parameters:**
- `client`: SyncClient instance
- `name`: Database name

**Returns:** `DatabaseDao` instance

**Raises:** `DatabaseException` if database already exists

**Example:**
```python
db = DatabaseDao.create(client, "mydb")
```

#### `delete(client, name)`

Delete a database.

```python
DatabaseDao.delete(client: Client, name: str) -> bool
```

**Parameters:**
- `client`: SyncClient instance
- `name`: Database name

**Returns:** `bool` - True if successful

**Example:**
```python
DatabaseDao.delete(client, "mydb")
```

#### `list_databases(client)`

List all databases on the server.

```python
DatabaseDao.list_databases(client: Client) -> List[str]
```

**Returns:** List of database names

**Example:**
```python
databases = DatabaseDao.list_databases(client)
print(f"Databases: {databases}")
```

### Constructor

```python
DatabaseDao(client: Client, database_name: str, driver: Driver = Driver.HTTP)
```

**Parameters:**
- `client`: SyncClient instance
- `database_name`: Name of the database to connect to
- `driver`: Driver type (HTTP or PSYCOPG, default: HTTP)

**Example:**
```python
db = DatabaseDao(client, "mydb")
```

### Core Methods

#### `query()`

Execute a query on the database.

```python
query(
    language: str,
    command: str,
    limit: Optional[int] = None,
    params: Optional[Any] = None,
    serializer: Optional[str] = None,
    session_id: Optional[str] = None,
    is_command: bool = False,
    retry_on_idempotent_error: bool = True
) -> Union[str, List, dict]
```

**Parameters:**
- `language` (str): Query language ("sql", "sqlscript", "graphql", "cypher", "gremlin", "mongo")
- `command` (str): The query/command to execute
- `limit` (int, optional): Maximum number of results
- `params` (dict, optional): Query parameters
- `serializer` (str, optional): Result serializer ("graph" or "record")
- `session_id` (str, optional): Transaction session ID
- `is_command` (bool, optional): Set to True for DDL/DML operations (CREATE, INSERT, UPDATE, DELETE)
- `retry_on_idempotent_error` (bool, optional): Automatically retry non-idempotent queries as commands

**Returns:** Query results (list of dicts, dict, or string)

**Raises:**
- `ValidationException`: Invalid parameters
- `QueryParsingException`: Query syntax error
- `TransactionException`: Transaction error

**Examples:**

```python
# SELECT query (read-only, is_command=False by default)
result = db.query("sql", "SELECT FROM Person WHERE age > 25")

# INSERT (requires is_command=True)
db.query("sql", "INSERT INTO Person SET name = 'John', age = 30", is_command=True)

# CREATE (requires is_command=True)
db.query("sql", "CREATE VERTEX TYPE Person IF NOT EXISTS", is_command=True)

# Query with parameters
result = db.query("sql", "SELECT FROM Person WHERE name = :name", params={"name": "John"})

# Query with limit
result = db.query("sql", "SELECT FROM Person", limit=10)
```

### Transaction Methods

#### `begin_transaction()`

Begin a new transaction.

```python
begin_transaction(isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED) -> str
```

**Parameters:**
- `isolation_level`: Transaction isolation level (READ_COMMITTED or REPEATABLE_READ)

**Returns:** Session ID (string)

**Example:**
```python
session_id = db.begin_transaction()
```

#### `commit_transaction()`

Commit a transaction.

```python
commit_transaction(session_id: str) -> None
```

**Parameters:**
- `session_id`: Session ID from `begin_transaction()`

**Example:**
```python
db.commit_transaction(session_id)
```

#### `rollback_transaction()`

Rollback a transaction.

```python
rollback_transaction(session_id: str) -> None
```

**Parameters:**
- `session_id`: Session ID from `begin_transaction()`

**Example:**
```python
db.rollback_transaction(session_id)
```

#### `execute_transaction()`

Execute multiple queries in a transaction with automatic retry.

```python
execute_transaction(
    queries: List[str],
    max_retries: int = 3,
    isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED
) -> List[Any]
```

**Parameters:**
- `queries`: List of SQL queries to execute
- `max_retries`: Maximum retry attempts
- `isolation_level`: Transaction isolation level

**Returns:** List of results for each query

**Example:**
```python
queries = [
    "INSERT INTO Person SET name = 'Alice', age = 28",
    "INSERT INTO Person SET name = 'Bob', age = 32"
]
results = db.execute_transaction(queries)
```

### Bulk Operations

#### `bulk_insert()`

Insert multiple records efficiently.

```python
bulk_insert(
    type_name: str,
    records: List[Dict[str, Any]],
    batch_size: int = 1000
) -> int
```

**Parameters:**
- `type_name`: Type/table name
- `records`: List of record dictionaries
- `batch_size`: Number of records per batch

**Returns:** Number of records inserted

**Example:**
```python
records = [
    {"name": "Alice", "age": 28},
    {"name": "Bob", "age": 32},
    {"name": "Charlie", "age": 25}
]
count = db.bulk_insert("Person", records)
print(f"Inserted {count} records")
```

#### `bulk_upsert()`

Insert or update multiple records based on a key field.

```python
bulk_upsert(
    type_name: str,
    records: List[Dict[str, Any]],
    key_field: str,
    batch_size: int = 1000
) -> int
```

**Parameters:**
- `type_name`: Type/table name
- `records`: List of record dictionaries
- `key_field`: Field name to use as unique key
- `batch_size`: Number of records per batch

**Returns:** Number of records upserted

**Example:**
```python
records = [
    {"email": "alice@example.com", "name": "Alice", "age": 28},
    {"email": "bob@example.com", "name": "Bob", "age": 32}
]
count = db.bulk_upsert("Person", records, key_field="email")
```

#### `bulk_delete()`

Delete multiple records based on conditions.

```python
bulk_delete(
    type_name: str,
    conditions: List[str],
    batch_size: int = 1000
) -> int
```

**Parameters:**
- `type_name`: Type/table name
- `conditions`: List of WHERE conditions
- `batch_size`: Number of deletes per batch

**Returns:** Number of records deleted

**Example:**
```python
conditions = ["age < 18", "active = false"]
count = db.bulk_delete("Person", conditions)
```

### Vector Operations

> **Note:** Vector similarity search is not currently supported by this driver. The methods below exist in the codebase but do not perform actual vector similarity calculations. You can store vector embeddings as arrays and retrieve them, but similarity search functions (cosine, euclidean, etc.) are not implemented.

#### `vector_search()`

**Status:** ⚠️ Not fully implemented - stores and retrieves vectors but does not perform similarity calculations.

Search for similar vectors.

```python
vector_search(
    type_name: str,
    embedding_field: str,
    query_vector: List[float],
    limit: int = 10,
    metric: str = "cosine"
) -> List[Dict[str, Any]]
```

**Parameters:**
- `type_name`: Type containing vectors
- `embedding_field`: Field name containing embeddings
- `query_vector`: Query vector (currently not used for similarity)
- `limit`: Number of results
- `metric`: Distance metric ("cosine", "euclidean", "dot") - currently ignored

**Returns:** List of matching records (without similarity scores)

**Current Behavior:**
```python
# This will store the vector but NOT perform similarity search
query_vector = [0.1, 0.2, 0.3, 0.4, 0.5]
results = db.vector_search("DocRecord", "embedding", query_vector, limit=5)
# Returns records but does NOT sort by similarity to query_vector
```

**Recommended Alternative:**
```python
# Store vectors as arrays
db.query("sql", "CREATE VERTEX TYPE DocRecord IF NOT EXISTS", is_command=True)
db.query("sql", """
    INSERT INTO DocRecord SET 
    title = 'Example',
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
""", is_command=True)

# Retrieve vectors (similarity calculation must be done in your application)
records = db.query("sql", "SELECT title, embedding FROM DocRecord")
# Perform your own similarity calculation in Python
```

#### `create_vector_index()`

**Status:** ⚠️ Exists but limited functionality - does not create specialized vector indexes.

Create an index on a vector field.

```python
create_vector_index(
    type_name: str,
    property_name: str,
    dimensions: int,
    metric: str = "cosine"
) -> bool
```

**Parameters:**
- `type_name`: Type name
- `property_name`: Field name containing vectors
- `dimensions`: Vector dimensionality (not currently validated)
- `metric`: Distance metric (currently ignored)

**Returns:** True if successful

**Current Behavior:**
```python
# This creates a basic property but not a specialized vector index
db.create_vector_index("DocRecord", "embedding", dimensions=384)
# Does NOT create an optimized vector similarity search index
```

**Note:** For actual vector similarity search with ArcadeDB, you may need to:
1. Use ArcadeDB's Java API directly (if vector support is available in your ArcadeDB version)
2. Implement similarity calculations in your Python application
3. Use an external vector database (Pinecone, Weaviate, Milvus, etc.) alongside ArcadeDB


### Utility Methods

#### `get_records()`

Get all records of specific types with filtering.

```python
get_records(
    type_names: Union[str, List[str]],
    where_clause: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `type_names`: Single type name or list of type names
- `where_clause`: Optional WHERE clause
- `limit`: Optional result limit

**Returns:** List of records

**Example:**
```python
# Get all people
people = db.get_records("Person")

# Get with filter
adults = db.get_records("Person", where_clause="age >= 18")

# Multiple types
records = db.get_records(["Person", "Customer"], limit=100)
```

#### `safe_delete_all()`

Safely delete all records from a type in batches.

```python
safe_delete_all(
    type_name: str,
    batch_size: int = 1000,
    max_retries: int = 3
) -> int
```

**Parameters:**
- `type_name`: Type to delete from
- `batch_size`: Records per batch
- `max_retries`: Maximum retry attempts

**Returns:** Number of records deleted

**Example:**
```python
deleted = db.safe_delete_all("Person", batch_size=500)
print(f"Deleted {deleted} records")
```

---

## Exceptions

### Exception Hierarchy

All exceptions inherit from `ArcadeDBException`.

```
ArcadeDBException
├── LoginFailedException
├── ConnectionException
├── DatabaseException
├── SchemaException
├── QueryParsingException
├── TransactionException
├── ValidationException
├── BulkOperationException
└── VectorOperationException
```

### ArcadeDBException

Base exception for all ArcadeDB errors.

**Attributes:**
- `message` (str): Error message
- `java_error_code` (str): Java exception class name
- `detail` (str): Detailed error information

**Example:**
```python
from arcadedb_python import ArcadeDBException

try:
    db.query("sql", "INVALID SQL")
except ArcadeDBException as e:
    print(f"Error: {e.message}")
    print(f"Detail: {e.detail}")
```

### Specific Exceptions

#### QueryParsingException

Raised when a query has syntax errors.

**Additional Attributes:**
- `query` (str): The query that failed

```python
from arcadedb_python import QueryParsingException

try:
    db.query("sql", "SELECT * FORM Person")  # typo: FORM
except QueryParsingException as e:
    print(f"Query error: {e.message}")
    print(f"Query: {e.query}")
```

#### TransactionException

Raised for transaction-related errors.

**Additional Attributes:**
- `session_id` (str): Transaction session ID
- `is_idempotent_error` (bool): Whether the error is safe to retry

```python
from arcadedb_python import TransactionException

try:
    db.execute_transaction(queries)
except TransactionException as e:
    if e.is_idempotent_error:
        print("Safe to retry")
```

#### BulkOperationException

Raised during bulk operations.

**Additional Attributes:**
- `failed_records` (int): Number of failed records
- `total_records` (int): Total number of records

```python
from arcadedb_python import BulkOperationException

try:
    db.bulk_insert("Person", records)
except BulkOperationException as e:
    print(f"Failed: {e.failed_records}/{e.total_records}")
```

---

## Configuration

### Environment Variables

You can configure the driver using environment variables:

```bash
# API endpoint (default: /api/v1)
export ARCADE_API_ENDPOINT=/api/v1

# Retry settings
export ARCADE_API_RETRY_MAX=3
export ARCADE_API_RETRY_DELAY=1
export ARCADE_API_RETRY_BACKOFF=2
```

### Available Query Languages

- `sql` - SQL (default)
- `sqlscript` - SQL Script
- `graphql` - GraphQL
- `cypher` - openCypher
- `gremlin` - Gremlin
- `mongo` - MongoDB Query Language

> **Note:** For large operations, ArcadeDB's native SQL or Java API will have better performance than openCypher or Gremlin.

### Isolation Levels

```python
from arcadedb_python import DatabaseDao

# Available levels
DatabaseDao.IsolationLevel.READ_COMMITTED
DatabaseDao.IsolationLevel.REPEATABLE_READ
```

### Driver Types

```python
from arcadedb_python import DatabaseDao

# Available drivers
DatabaseDao.Driver.HTTP  # HTTP REST API (default)
DatabaseDao.Driver.PSYCOPG  # PostgreSQL protocol (requires psycopg)
```

---

## Complete Example

```python
from arcadedb_python import DatabaseDao, SyncClient, ArcadeDBException

# Connect
client = SyncClient("localhost", 2480, username="root", password="playwithdata")

# Create database
if not DatabaseDao.exists(client, "myapp"):
    db = DatabaseDao.create(client, "myapp")
else:
    db = DatabaseDao(client, "myapp")

# Create schema
db.query("sql", "CREATE VERTEX TYPE User IF NOT EXISTS", is_command=True)

# Insert with transaction
try:
    session_id = db.begin_transaction()
    db.query("sql", "INSERT INTO User SET name = 'Alice', email = 'alice@example.com'", 
             is_command=True, session_id=session_id)
    db.commit_transaction(session_id)
    print("Transaction committed")
except ArcadeDBException as e:
    db.rollback_transaction(session_id)
    print(f"Transaction rolled back: {e}")

# Bulk insert
users = [
    {"name": "Bob", "email": "bob@example.com"},
    {"name": "Charlie", "email": "charlie@example.com"}
]
count = db.bulk_insert("User", users)
print(f"Inserted {count} users")

# Query
results = db.query("sql", "SELECT FROM User WHERE name LIKE 'A%'")
for user in results:
    print(f"User: {user['name']} ({user['email']})")

# Store vectors (no similarity search - see Vector Operations section)
db.query("sql", "CREATE VERTEX TYPE DocRecord IF NOT EXISTS", is_command=True)
db.query("sql", """
    INSERT INTO DocRecord SET 
    title = 'Document 1',
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
""", is_command=True)

# Retrieve documents with embeddings
docs = db.query("sql", "SELECT title, embedding FROM DocRecord")
print(f"Found {len(docs)} documents with embeddings")
```

---

## Additional Resources

- **ArcadeDB Documentation**: https://docs.arcadedb.com
- **GitHub Repository**: https://github.com/stevereiner/arcadedb-python
- **PyPI Package**: https://pypi.org/project/arcadedb-python/
- **Issue Tracker**: https://github.com/stevereiner/arcadedb-python/issues

