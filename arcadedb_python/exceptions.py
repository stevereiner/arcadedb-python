"""
ArcadeDB Python Driver Exceptions

This module provides typed exceptions for better error handling and debugging.
"""

from typing import Optional, Dict, Any


class ArcadeDBException(Exception):
    """Base exception for all ArcadeDB-related errors."""
    
    def __init__(self, message: str, java_error_code: Optional[str] = None, 
                 detail: Optional[str] = None, response_data: Optional[Dict[str, Any]] = None):
        self.message = message
        self.java_error_code = java_error_code
        self.detail = detail
        self.response_data = response_data or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message


class LoginFailedException(ArcadeDBException):
    """Raised when authentication fails."""
    pass


class QueryParsingException(ArcadeDBException):
    """Raised when SQL/Cypher query parsing fails."""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        self.query = query
        super().__init__(message, **kwargs)
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.query:
            return f"{base_msg}\nQuery: {self.query}"
        return base_msg


class TransactionException(ArcadeDBException):
    """Raised when transaction operations fail."""
    
    def __init__(self, message: str, session_id: Optional[str] = None, 
                 is_idempotent_error: bool = False, **kwargs):
        self.session_id = session_id
        self.is_idempotent_error = is_idempotent_error
        super().__init__(message, **kwargs)


class SchemaException(ArcadeDBException):
    """Raised when schema operations fail."""
    
    def __init__(self, message: str, type_name: Optional[str] = None, **kwargs):
        self.type_name = type_name
        super().__init__(message, **kwargs)


class DatabaseException(ArcadeDBException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str, database_name: Optional[str] = None, **kwargs):
        self.database_name = database_name
        super().__init__(message, **kwargs)


class ConnectionException(ArcadeDBException):
    """Raised when connection to ArcadeDB fails."""
    pass


class ValidationException(ArcadeDBException):
    """Raised when input validation fails."""
    pass


class BulkOperationException(ArcadeDBException):
    """Raised when bulk operations fail."""
    
    def __init__(self, message: str, failed_records: Optional[int] = None, 
                 total_records: Optional[int] = None, **kwargs):
        self.failed_records = failed_records
        self.total_records = total_records
        super().__init__(message, **kwargs)
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.failed_records is not None and self.total_records is not None:
            return f"{base_msg} ({self.failed_records}/{self.total_records} records failed)"
        return base_msg


class VectorOperationException(ArcadeDBException):
    """Raised when vector operations fail."""
    
    def __init__(self, message: str, dimensions: Optional[int] = None, **kwargs):
        self.dimensions = dimensions
        super().__init__(message, **kwargs)


def parse_error_response(response_data: Dict[str, Any], query: Optional[str] = None) -> ArcadeDBException:
    """
    Parse an error response from ArcadeDB and return the appropriate exception.
    
    Args:
        response_data: The error response from ArcadeDB
        query: The query that caused the error (optional)
        
    Returns:
        An appropriate ArcadeDBException subclass
    """
    error_msg = response_data.get('error', 'Unknown error')
    detail = response_data.get('detail', '')
    exception_type = response_data.get('exception', '')
    
    # Security/Authentication errors
    if exception_type == "com.arcadedb.server.security.ServerSecurityException":
        return LoginFailedException(error_msg, java_error_code=exception_type, 
                                  detail=detail, response_data=response_data)
    
    # SQL Parsing errors
    if "CommandSQLParsingException" in exception_type or "parsing" in error_msg.lower():
        return QueryParsingException(error_msg, query=query, java_error_code=exception_type,
                                   detail=detail, response_data=response_data)
    
    # Transaction errors
    if "transaction" in error_msg.lower() or "idempotent" in error_msg.lower():
        is_idempotent_error = "idempotent" in error_msg.lower()
        return TransactionException(error_msg, is_idempotent_error=is_idempotent_error,
                                  java_error_code=exception_type, detail=detail, 
                                  response_data=response_data)
    
    # Schema errors
    if "schema" in error_msg.lower() or "type" in error_msg.lower() and "not found" in error_msg.lower():
        return SchemaException(error_msg, java_error_code=exception_type,
                             detail=detail, response_data=response_data)
    
    # Database errors
    if "database" in error_msg.lower():
        return DatabaseException(error_msg, java_error_code=exception_type,
                                detail=detail, response_data=response_data)
    
    # Default to base exception
    return ArcadeDBException(error_msg, java_error_code=exception_type,
                           detail=detail, response_data=response_data)
