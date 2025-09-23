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
from arcadedb_python import DatabaseDao

# Connect to ArcadeDB
db = DatabaseDao(
    host="localhost",
    port=2480,
    database="mydb",
    username="root",
    password="playwithdata"
)

# Execute SQL queries
result = db.query("sql", "SELECT FROM V LIMIT 10")
print(result)

# Create vertices and edges
db.command("sql", "CREATE VERTEX TYPE Person")
db.command("sql", "INSERT INTO Person SET name = 'John', age = 30")

# Graph traversal
result = db.query("sql", """
    MATCH {type: Person, as: person} 
    RETURN person.name, person.age
""")
```

### Configuration

```python
from arcadedb_python import ArcadeDBConfig, DatabaseDao

# Using configuration object
config = ArcadeDBConfig(
    host="localhost",
    port=2480,
    username="root",
    password="playwithdata"
)

db = DatabaseDao.from_config(config, "mydb")
```

### Async Operations

```python
import asyncio
from arcadedb_python import DatabaseDao

async def main():
    db = DatabaseDao("localhost", 2480, "mydb", "root", "playwithdata")
    
    # Async query execution
    result = await db.query_async("sql", "SELECT FROM V LIMIT 10")
    print(result)

asyncio.run(main())
```

## Advanced Usage

### Working with Different Data Models

```python
# Document operations
db.command("sql", "CREATE DOCUMENT TYPE Product")
db.command("sql", """
    INSERT INTO Product CONTENT {
        "name": "Laptop",
        "price": 999.99,
        "specs": {
            "cpu": "Intel i7",
            "ram": "16GB"
        }
    }
""")

# Graph operations
db.command("sql", "CREATE VERTEX TYPE Customer")
db.command("sql", "CREATE EDGE TYPE Purchased")
db.command("sql", """
    CREATE EDGE Purchased 
    FROM (SELECT FROM Customer WHERE name = 'John')
    TO (SELECT FROM Product WHERE name = 'Laptop')
    SET date = date(), amount = 999.99
""")

# Key-Value operations
db.command("sql", "CREATE DOCUMENT TYPE Settings")
db.command("sql", "INSERT INTO Settings SET key = 'theme', value = 'dark'")

# Time-Series operations
db.command("sql", "CREATE VERTEX TYPE Sensor")
db.command("sql", """
    INSERT INTO Sensor SET 
    sensor_id = 'temp_01', 
    timestamp = sysdate(), 
    temperature = 23.5
""")
```

### Vector Search (for AI/ML applications)

```python
# Store embeddings
db.command("sql", """
    CREATE VERTEX TYPE Document SET 
    title = 'AI Research Paper',
    embedding = [0.1, 0.2, 0.3, ...],  # Your vector embeddings
    content = 'Full document text...'
""")

# Vector similarity search
result = db.query("sql", """
    SELECT title, content, 
           cosine_similarity(embedding, [0.1, 0.2, 0.3, ...]) as similarity
    FROM Document 
    ORDER BY similarity DESC 
    LIMIT 10
""")
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | str | "localhost" | ArcadeDB server hostname |
| `port` | int | 2480 | ArcadeDB server port |
| `username` | str | "root" | Database username |
| `password` | str | None | Database password |
| `database` | str | None | Database name |
| `use_ssl` | bool | False | Enable SSL connection |
| `timeout` | int | 30 | Request timeout in seconds |
| `pool_size` | int | 10 | Connection pool size |

## Requirements

- **Python**: 3.8 or higher
- **ArcadeDB**: Version 23.10 or higher
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