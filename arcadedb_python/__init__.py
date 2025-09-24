"""ArcadeDB Python Driver.

A Python driver for ArcadeDB - Multi-Model Database with Graph, Document, 
Key-Value, Vector, and Time-Series support.

This package provides a comprehensive Python interface to ArcadeDB, enabling
developers to work with all of ArcadeDB's data models through a unified API.

Example:
    Basic usage:
    
    >>> from arcadedb_python import DatabaseDao
    >>> db = DatabaseDao("localhost", 2480, "mydb", "root", "password")
    >>> result = db.query("sql", "SELECT FROM V LIMIT 10")
    >>> print(result)

Classes:
    DatabaseDao: Main database access object for executing queries
    ArcadeDBConfig: Configuration class for connection settings
    
For more information, visit: https://docs.arcadedb.com/
"""

__version__ = "0.3.0"
__author__ = "Adams Rosales, ExtReMLapin, Steve Reiner"
__email__ = ""
__license__ = "Apache-2.0"

# Import main classes for easy access
from arcadedb_python.dao.database import DatabaseDao
from arcadedb_python.api.sync import SyncClient
from arcadedb_python.api.client import Client
from arcadedb_python.exceptions import (
    ArcadeDBException,
    LoginFailedException,
    QueryParsingException,
    TransactionException,
    SchemaException,
    DatabaseException,
    ConnectionException,
    ValidationException,
    BulkOperationException,
    VectorOperationException,
)

__all__ = [
    "DatabaseDao",
    "SyncClient", 
    "Client",
    # Exceptions
    "ArcadeDBException",
    "LoginFailedException",
    "QueryParsingException",
    "TransactionException",
    "SchemaException",
    "DatabaseException",
    "ConnectionException",
    "ValidationException",
    "BulkOperationException",
    "VectorOperationException",
    "__version__",
]
