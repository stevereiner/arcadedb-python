# ArcadeDB Python Driver

[![PyPI version](https://badge.fury.io/py/arcadedb-python.svg)](https://badge.fury.io/py/arcadedb-python)
[![Python versions](https://img.shields.io/pypi/pyversions/arcadedb-python.svg)](https://pypi.org/project/arcadedb-python/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A comprehensive Python driver for [ArcadeDB](https://arcadedb.com) - the Multi-Model Database that supports Graph, Document, Key-Value, Vector, and Time-Series models in a single engine.

## Credits & Attribution

This driver builds upon the excellent work of the original ArcadeDB Python driver contributors:

- **Adams Rosales** ([@adaros92](https://github.com/adaros92)) - Original [arcadedb-python-driver](https://github.com/adaros92/arcadedb-python-driver)
- **ExtReMLapin** ([@ExtReMLapin](https://github.com/ExtReMLapin)) - Core contributor and enhancements
- **ArcadeDB Team** - The amazing [ArcadeDB](https://github.com/ArcadeData/arcadedb) database engine

This modernized version enhances the original work with updated packaging, comprehensive documentation, and production-ready features while maintaining full compatibility with the [ArcadeDB](https://arcadedb.com/) database.

## Features

- **Multi-Model Support**: Work with Graph, Document, Key-Value, Vector, and Time-Series data models
- **High Performance**: Optimized for speed with native ArcadeDB protocols
- **Full API Coverage**: Complete access to ArcadeDB's REST API and SQL capabilities
- **Type Safety**: Comprehensive type hints for better development experience
- **Async Support**: Both synchronous and asynchronous operation modes
- **Connection Pooling**: Efficient connection management for production use
- **Comprehensive Testing**: Extensive test suite ensuring reliability

## Installation

### Using UV (Recommended)

```bash
# Install uv if not already installed
pip install uv

# Create virtual environment and install
uv venv
uv pip install arcadedb-python
```

### Using Pip

```bash
pip install arcadedb-python
```

### Optional Dependencies

```bash
# PostgreSQL driver support
uv pip install arcadedb-python[postgresql]
# or: pip install arcadedb-python[postgresql]

# Cypher syntax highlighting
uv pip install arcadedb-python[cypher]
# or: pip install arcadedb-python[cypher]

# All optional features
uv pip install arcadedb-python[full]
# or: pip install arcadedb-python[full]

# Development dependencies
uv pip install arcadedb-python[dev]
# or: pip install arcadedb-python[dev]
```

## Quick Start

### Basic Usage

```python
from arcadedb_python import DatabaseDao, SyncClient

# Step 1: Create a client connection
client = SyncClient(
    host="localhost",
    port=2480,
    username="root",
    password="playwithdata"
)

# Step 2: Connect to database (or create it)
if not DatabaseDao.exists(client, "mydb"):
    db = DatabaseDao.create(client, "mydb")
else:
    db = DatabaseDao(client, "mydb")

# Step 3: Create schema (DDL requires is_command=True)
db.query("sql", "CREATE VERTEX TYPE Person IF NOT EXISTS", is_command=True)

# Step 4: Insert data (DML requires is_command=True)
db.query("sql", "INSERT INTO Person SET name = 'John', age = 30", is_command=True)

# Step 5: Query data
result = db.query("sql", "SELECT FROM Person LIMIT 10")
print(result)

# Step 6: Graph traversal
result = db.query("sql", """
    MATCH {type: Person, as: person} 
    RETURN person.name, person.age
""")
print(result)
```

### Important Notes

- **Use `SyncClient`** to create connections, not `DatabaseDao` directly
- **Use `is_command=True`** for DDL/DML operations (CREATE, INSERT, UPDATE, DELETE)
- **SELECT queries** don't need `is_command=True` (it defaults to False)
- **Create vertex types first** before querying (V and E types don't exist by default)
```

## API Documentation

For complete API reference including all methods, parameters, exceptions, and detailed examples:

**📚 [docs/API.md](docs/API.md)** - Comprehensive API documentation covering:
- `SyncClient` - Connection management
- `DatabaseDao` - All database operations (query, transactions, bulk operations)
- Exception handling and error types
- Configuration options
- Complete code examples

## Examples

### Available Examples

**[examples/quickstart_example.py](examples/quickstart_example.py)**
- Complete walkthrough of all Quick Start code
- All data models: Graph, Document, Key-Value, Time-Series, Vector storage
- Step-by-step explanations
- Error handling examples

**[examples/test_query_languages.py](examples/test_query_languages.py)**
- openCypher query examples
- Gremlin query examples
- Database creation and cleanup

### Running Examples

```bash
# Complete quickstart with all features
python examples/quickstart_example.py

# Test openCypher and Gremlin queries
python examples/test_query_languages.py
```

**Requirements:** ArcadeDB must be running on `localhost:2480` with default credentials (`root`/`playwithdata`)

## Advanced Usage

### Working with Different Data Models

```python
# Document operations
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

# Graph operations
db.query("sql", "CREATE VERTEX TYPE Customer IF NOT EXISTS", is_command=True)
db.query("sql", "CREATE EDGE TYPE Purchased IF NOT EXISTS", is_command=True)
db.query("sql", """
    CREATE EDGE Purchased 
    FROM (SELECT FROM Customer WHERE name = 'John')
    TO (SELECT FROM Product WHERE name = 'Laptop')
    SET date = sysdate(), amount = 999.99
""", is_command=True)

# Key-Value operations
db.query("sql", "CREATE DOCUMENT TYPE Settings IF NOT EXISTS", is_command=True)
db.query("sql", "INSERT INTO Settings SET key = 'theme', value = 'dark'", is_command=True)

# Time-Series operations
db.query("sql", "CREATE VERTEX TYPE Sensor IF NOT EXISTS", is_command=True)
db.query("sql", """
    INSERT INTO Sensor SET 
    sensor_id = 'temp_01', 
    timestamp = sysdate(), 
    temperature = 23.5
""", is_command=True)
```

### Vector Search (for AI/ML applications)

```python
# Note: Vector similarity search is not currently supported by this driver
# You can store vector embeddings as arrays

# Store embeddings
db.query("sql", "CREATE VERTEX TYPE DocRecord IF NOT EXISTS", is_command=True)
db.query("sql", """
    INSERT INTO DocRecord SET 
    title = 'AI Research Paper',
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5],
    content = 'Full document text...'
""", is_command=True)

# Query documents with embeddings
result = db.query("sql", "SELECT title, embedding FROM DocRecord WHERE title = 'AI Research Paper'")
```

### Using openCypher

```python
# Note: openCypher support may have different performance characteristics than native SQL
# For large operations, consider using ArcadeDB's native SQL or Java API

# Create nodes
db.query("cypher", "CREATE (p:Person {name: 'John', age: 30})", is_command=True)
db.query("cypher", "CREATE (p:Person {name: 'Jane', age: 25})", is_command=True)

# Create relationship
db.query("cypher", """
    MATCH (a:Person {name: 'John'}), (b:Person {name: 'Jane'})
    CREATE (a)-[:KNOWS]->(b)
""", is_command=True)

# Query with openCypher
result = db.query("cypher", "MATCH (p:Person) RETURN p.name, p.age")
print(result)
```

### Using Gremlin

```python
# Note: Gremlin support may have different performance characteristics than native SQL
# For large operations, consider using ArcadeDB's native SQL or Java API

# Add vertices
db.query("gremlin", "g.addV('Person').property('name', 'John').property('age', 30)", is_command=True)
db.query("gremlin", "g.addV('Person').property('name', 'Jane').property('age', 25)", is_command=True)

# Query with Gremlin
result = db.query("gremlin", "g.V().hasLabel('Person').values('name')")
print(result)

# Traversal
result = db.query("gremlin", "g.V().hasLabel('Person').has('age', gt(20)).values('name', 'age')")
print(result)
```

## Configuration Options

### SyncClient Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | "localhost" | ArcadeDB server hostname |
| `port` | int | 2480 | ArcadeDB server port |
| `username` | str | None | Database username |
| `password` | str | None | Database password |
| `protocol` | str | "http" | Protocol ("http" or "https") |

### DatabaseDao.query() Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | str | Required | Query language: "sql", "cypher", "gremlin", "graphql", "mongo" |
| `command` | str | Required | The query/command to execute |
| `is_command` | bool | False | Set True for DDL/DML (CREATE, INSERT, UPDATE, DELETE) |
| `limit` | int | None | Maximum number of results |
| `params` | dict | None | Query parameters |
| `session_id` | str | None | Transaction session ID |

## Requirements

- **Python**: 3.10 or higher
- **ArcadeDB**: Version 25.8.1 or higher
- **Dependencies**: 
  - `requests` >= 2.25.0
  - `retry` >= 0.9.2

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/stevereiner/arcadedb-python.git
cd arcadedb-python

# Install uv (if not already installed)
pip install uv

# Create virtual environment and install dependencies
uv venv
uv pip install -e .[dev]

# Run tests
uv run pytest

# Run linting
uv run black .
uv run isort .
uv run flake8
uv run mypy arcadedb_python
```

### Building the Package

```bash
# Build the package
uv build

# Check the built package
uv run twine check dist/*
```

### Running ArcadeDB for Development

```bash
# Using Docker
docker run -d --name arcadedb \
  -p 2480:2480 -p 2424:2424 \
  -e JAVA_OPTS="-Darcadedb.server.rootPassword=playwithdata" \
  arcadedata/arcadedb:latest

# Access ArcadeDB Studio at http://localhost:2480
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Links

### This Project
- **GitHub**: https://github.com/stevereiner/arcadedb-python
- **PyPI**: https://pypi.org/project/arcadedb-python/
- **Issues**: https://github.com/stevereiner/arcadedb-python/issues

### ArcadeDB
- **Homepage**: https://arcadedb.com
- **Documentation**: https://docs.arcadedb.com
- **Main Repository**: https://github.com/ArcadeData/arcadedb

### Original Contributors
- **Adams Rosales**: https://github.com/adaros92/arcadedb-python-driver
- **ExtReMLapin**: https://github.com/ExtReMLapin

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.