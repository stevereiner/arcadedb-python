"""ArcadeDB Python Driver.

A Python driver for ArcadeDB - Multi-Model Database with Graph, Document, 
Key-Value, Vector, and Time-Series support.

This package provides a comprehensive Python interface to ArcadeDB, enabling
developers to work with all of ArcadeDB's data models through a unified API.

Example:
    Basic usage:
    
    >>> from arcadedb_python import DatabaseDao, SyncClient
    >>> client = SyncClient("localhost", 2480, username="root", password="playwithdata")
    >>> db = DatabaseDao(client, "mydb")
    >>> result = db.query("sql", "SELECT FROM Person LIMIT 10")
    >>> print(result)

Classes:
    SyncClient: HTTP client for connecting to ArcadeDB
    DatabaseDao: Main database access object for executing queries and commands
    Client: Abstract base class for database clients

Constants:
    AVAILABLE_LANGUAGES: Set of supported query languages 
        {"sql", "sqlscript", "graphql", "opencypher", "gremlin", "mongo"}

Logging:
    configure_logging: Configure log levels for the package or individual modules
    get_logger: Retrieve a named logger by module path or short alias
    LOGGER_NAMES: Mapping of short aliases to full logger names

Exceptions:
    ArcadeDBException: Base exception class
    LoginFailedException: Authentication failure
    QueryParsingException: Query syntax error
    TransactionException: Transaction error
    SchemaException: Schema-related error
    DatabaseException: Database operation error
    ConnectionException: Connection error
    ValidationException: Input validation error
    BulkOperationException: Bulk operation error
    VectorOperationException: Vector operation error
    
For more information, visit: https://docs.arcadedb.com/
"""

__version__ = "0.4.0"
__author__ = "Steve Reiner, Adams Rosales, ExtReMLapin"
__email__ = ""
__license__ = "Apache-2.0"

# Import main classes for easy access
from arcadedb_python.dao.database import DatabaseDao
from arcadedb_python.api.sync import SyncClient
from arcadedb_python.api.client import Client
from arcadedb_python.api.config import AVAILABLE_LANGUAGES
from arcadedb_python.logging_config import configure_logging, get_logger, LOGGER_NAMES
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
    "AVAILABLE_LANGUAGES",
    # Logging
    "configure_logging",
    "get_logger",
    "LOGGER_NAMES",
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
