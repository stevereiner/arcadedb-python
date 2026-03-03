
from ..api.client import Client
from ..api import config
from ..exceptions import DatabaseException, ValidationException, QueryParsingException, TransactionException, BulkOperationException, VectorOperationException
from typing import Optional, Any, List, Union, Dict
from enum import Enum
import re
import json
import logging
logger = logging.getLogger(__name__)
try:
    import psycopg
    PSYCOPG_AVAILABLE = True
except ImportError:
    PSYCOPG_AVAILABLE = False
    psycopg = None

try:
    from pygments.lexers import get_lexer_by_name
    from pygments.token import string_to_tokentype
    try:
        # Try to get the Cypher lexer - might not be available
        cypher_lexer = get_lexer_by_name("cypher")
    except:
        try:
            # Fallback to SQL lexer
            cypher_lexer = get_lexer_by_name("sql")
        except:
            cypher_lexer = None
    
    if cypher_lexer:
        punctuation = string_to_tokentype("Token.Punctuation")
        global_var = string_to_tokentype("Token.Name.Variable.Global")
        string_liral = string_to_tokentype("Token.Literal.String")
        PYGMENTS_AVAILABLE = True
    else:
        PYGMENTS_AVAILABLE = False
except ImportError:
    PYGMENTS_AVAILABLE = False
    cypher_lexer = None


class DatabaseDao:
    """
    Class to work with ArcadeDB databases
    """

    class IsolationLevel(Enum):
        """Isolation levels for transactions"""
        READ_COMMITTED = "READ_COMMITTED"
        REPEATABLE_READ = "REPEATABLE_READ"
        
    class Driver(Enum):
        HTTP="HTTP"
        PSYCOPG="PSYCOPG"

    @staticmethod
    def exists(client, name: str) -> bool:
        """
        Check if a database exists.

        Parameters:
        - client (Client): The ArcadeDB client.
        - name (str): The name of the database.

        Returns:
        bool: True if the database exists, False otherwise.
        """
        response = client.get(f"{config.ARCADE_BASE_EXISTS_ENDPOINT}/{name}")
        return response

    @staticmethod
    def create(client: Client, name: str) -> 'DatabaseDao':
        """
        Create a new database.

        Parameters:
        - client (Client): The ArcadeDB client.
        - name (str): The name of the new database.

        Returns:
        DatabaseDao: An instance of DatabaseDao for the created database.

        Raises:
        - ValueError: If the database already exists.
        - ValueError: If the creation of the database fails.
        """
        if DatabaseDao.exists(client, name):
            raise DatabaseException(f"Database {name} already exists", database_name=name)

        ret = client.post(config.ARCADE_BASE_SERVER_ENDPOINT, {"command": f"create database {name}"})
        if ret == "ok":
            return DatabaseDao(client, name)
        else:
            raise DatabaseException(f"Could not create database {name}: {ret}", database_name=name)

    @staticmethod
    def delete(client: Client, name: str) -> bool:
        """
        Delete a database.

        Parameters:
        - client (Client): The ArcadeDB client.
        - name (str): The name of the database to be deleted.

        Returns:
        bool: True if the database is successfully deleted.

        Raises:
        - ValueError: If the database does not exist.
        - ValueError: If the deletion of the database fails.
        """
        if not DatabaseDao.exists(client, name):
            raise DatabaseException(f"Database {name} does not exist", database_name=name)
        ret = client.post(config.ARCADE_BASE_SERVER_ENDPOINT, {"command": f"drop database {name}"})
        if ret == "ok":
            return True
        else:
            raise DatabaseException(f"Could not drop database {name}: {ret}", database_name=name)

    @staticmethod
    def list_databases(client: Client) -> List:
        """
        List all databases.

        Parameters:
        - client (Client): The ArcadeDB client.

        Returns:
        str: The list of databases.
        """
        return client.get(config.ARCADE_BASE_LIST_DB_ENDPOINT)

    def __init__(
        self,
        client: Client,
        database_name: str,
        driver:Driver=Driver.HTTP
        
    ):
        """
        Initialize a DatabaseDao instance.

        Parameters:
        - client (Client): The ArcadeDB client.
        - database_name (str): The name of the database.

        Raises:
        - ValueError: If the database does not exist. Call create() to create a new database.
        """
        self.client = client
        self.database_name = database_name
        self.driver = driver

            
        if self.driver == self.Driver.PSYCOPG:
            if not PSYCOPG_AVAILABLE:
                raise ImportError("psycopg is required for PSYCOPG driver. Install with: pip install psycopg")
            port = self.client.port
            if client.port == 2480:
                print("Auto switching port to 5432 as we're using PSYCOPG driver")
                port = 5432
            self.connection = psycopg.connect(user=self.client.username, password=self.client.password,
                    host=self.client.host,
                    port=port,
                    dbname=self.database_name,
                    sslmode='disable'
                )
        else:
            self.connection = None
        if not DatabaseDao.exists(client, database_name):
            raise DatabaseException(f"Database {database_name} does not exist, call create()", database_name=database_name)
        
        
    cypher_var_regex = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_]*)')
    

    @staticmethod
    def cypher_formater(query: str, params: dict) -> str:
        if not PYGMENTS_AVAILABLE:
            # Fallback to simple parameter substitution if pygments not available
            import re

            def replace_param(match):
                param_name = match.group(1)
                if param_name in params:
                    value = params[param_name]
                    if isinstance(value, str):
                        escaped_value = value.replace('\\', '\\\\').replace("'", "\\'")
                        return f"'{escaped_value}'"
                    return str(value)
                return match.group(0)
            
            result = re.sub(r'\$([a-zA-Z_][a-zA-Z0-9_]*)', replace_param, query)
            return result, {}

        skipped_params = {}
        tokens = list(cypher_lexer.get_tokens(query))
        i = 0
        len_tokens = len(tokens)
        while i < len_tokens - 1:
            if tokens[i][0] == punctuation and tokens[i + 1][0] == global_var:
                var_name = tokens[i + 1][1]
                assert var_name in params, f"Variable {var_name} not found in the parameters"
                if isinstance(params[var_name], str) and '$' in params[var_name]:
                    skipped_params[var_name] = params[var_name]
                    i += 2
                    continue
                if isinstance(params[var_name], list):
                    skipped_params[var_name] = params[var_name]
                    i += 2
                    continue

                escaped_string = str(params[var_name]).replace("\\", "\\\\").replace("'", "\\'")
                tokens[i] = (string_liral, f"'{escaped_string}'")
                tokens.pop(i + 1)
                len_tokens -= 1
    
            i += 1
        return "".join([x[1] for x in tokens]), skipped_params
    
        

    def query(
        self,
        language: str,
        command: str,
        limit: Optional[int] = None,
        params: Optional[Any] = None,
        serializer: Optional[str] = None,
        session_id: Optional[str] = None,
        is_command: Optional[bool] = False,
        retry_on_idempotent_error: bool = True
    ) -> Union[str, List, dict]:
        """
        Execute a query on the database.

        Parameters:
        - language (str): The query language.
        - command (str): The query command.
        - limit (int): The limit on the number of results (optional).
        - params: The parameters for the query (optional).
        - serializer (str): The serializer for the query results (optional).
        - session_id: The session ID for the query (optional).
        - is_command: If the query is a command (optional), you need this to run non-idempotent commands.
        - retry_on_idempotent_error: If True, automatically retry non-idempotent queries as commands.

        Returns:
        str: The result of the query.
        """
        language = language.lower()
        if language not in config.AVAILABLE_LANGUAGES:
            raise ValidationException(f"Language {language} not supported. Available languages: {', '.join(config.AVAILABLE_LANGUAGES)}")
        if limit is not None and not isinstance(limit, int):
            raise ValidationException("Limit must be an integer")
        serializer = serializer.lower() if serializer else serializer
        if serializer not in {None, "graph", "record"}:
            raise ValidationException("Serializer must be None, 'graph' or 'record'")
        
        if language == "opencypher" and params:
            command, new_params = self.cypher_formater(command, params)
            params = new_params if len(new_params) > 0 else None
        payload = {
            "command": command,
            "language": language,
        }
        if limit is not None:
            payload["limit"] = limit
        if params is not None:
            payload["params"] = params
        if serializer is not None:
            if self.driver != self.Driver.HTTP:
                raise ValidationException("Serializer is only supported with HTTP driver")
            payload["serializer"] = serializer
        extra_headers = {}
        if session_id is not None:
            if self.driver != self.Driver.HTTP:
                raise ValidationException("Session ID is only supported with HTTP driver")
            extra_headers["arcadedb-session-id"] = session_id
        if self.driver == self.Driver.HTTP:
            try:
                # Try as regular query first
                endpoint = config.ARCADE_BASE_QUERY_ENDPOINT if is_command is False else config.ARCADE_BASE_COMMAND_ENDPOINT
                req = self.client.post(f"{endpoint}/{self.database_name}", payload, extra_headers=extra_headers)
                return req
                
            except TransactionException as e:
                # Check if this is an idempotent error and we should retry
                if (retry_on_idempotent_error and 
                    e.is_idempotent_error and 
                    not is_command):
                    
                    logger.info(f"Retrying non-idempotent query as command: {command[:100]}...")
                    
                    try:
                        # Retry as a command
                        req = self.client.post(f"{config.ARCADE_BASE_COMMAND_ENDPOINT}/{self.database_name}", 
                                             payload, extra_headers=extra_headers)
                        return req
                    except Exception as retry_error:
                        # If retry also fails, raise the original error with context
                        raise TransactionException(
                            f"Query failed as both regular query and command. Original error: {str(e)}. Retry error: {str(retry_error)}",
                            session_id=session_id,
                            is_idempotent_error=True
                        ) from e
                else:
                    # Re-raise the original exception
                    raise
                    
        else:
            # PostgreSQL driver
            with self.connection.cursor(row_factory=psycopg.rows.dict_row) as cursor:
                prefix = "" if language == "sql" else f"{{{language}}}"
                cursor.execute(query=prefix+command, params=params)
                return cursor.fetchall()

    def begin_transaction(self, isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED) -> str:

        """
        Begin a new transaction.

        Parameters:
        - isolation_level (IsolationLevel): The isolation level for the transaction (default: READ_COMMITTED).

        Returns:
        str: The session ID for the new transaction.
        """
        headers = self.client.post(f"{config.ARCADE_BASE_TRANSACTION_BEGIN_ENDPOINT}/{self.database_name}", {"isolationLevel": isolation_level.value}, return_headers=True)
        return headers["arcadedb-session-id"]

    def commit_transaction(self, session_id) -> None:
        """
        Commit a transaction.

        Parameters:
        - session_id: The session ID of the transaction to be committed.
        """
        self.client.post(f"{config.ARCADE_BASE_TRANSACTION_COMMIT_ENDPOINT}/{self.database_name}", {}, extra_headers={"arcadedb-session-id": session_id})

    def rollback_transaction(self, session_id) -> None:
        """
        Rollback a transaction.

        Parameters:
        - session_id: The session ID of the transaction to be rolled back.
        """
        self.client.post(f"{config.ARCADE_BASE_TRANSACTION_ROLLBACK_ENDPOINT}/{self.database_name}", {}, extra_headers={"arcadedb-session-id": session_id})

    def safe_delete_all(self, type_name: str, batch_size: int = 1000, 
                       session_id: Optional[str] = None) -> int:
        """
        Safely delete all records from a type using batched operations.
        
        This method works around ArcadeDB's non-idempotent query restrictions
        by using smaller batches and proper transaction handling.
        
        Parameters:
        - type_name (str): The type/table name to delete from
        - batch_size (int): Number of records to delete in each batch
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        int: Approximate number of records deleted
        
        Raises:
        TransactionException: If deletion fails
        """
        total_deleted = 0
        
        try:
            # First, try TRUNCATE TYPE if supported
            try:
                result = self.query("sql", f"TRUNCATE TYPE {type_name} UNSAFE", 
                                  session_id=session_id, is_command=True, 
                                  retry_on_idempotent_error=False)
                logger.info(f"Successfully truncated type {type_name}")
                return 0  # TRUNCATE doesn't return count
            except Exception as truncate_error:
                logger.debug(f"TRUNCATE failed for {type_name}: {truncate_error}")
                
            # Fallback to batched deletion
            while True:
                try:
                    # Get a batch of records to delete
                    records = self.query("sql", f"SELECT @rid FROM {type_name} LIMIT {batch_size}", 
                                       session_id=session_id)
                    
                    if not records or len(records) == 0:
                        break  # No more records to delete
                        
                    # Delete the batch
                    if isinstance(records, list):
                        rids = [record.get('@rid') for record in records if '@rid' in record]
                        if rids:
                            rid_list = "', '".join(rids)
                            delete_query = f"DELETE FROM {type_name} WHERE @rid IN ['{rid_list}']"
                            self.query("sql", delete_query, session_id=session_id, 
                                     is_command=True, retry_on_idempotent_error=False)
                            total_deleted += len(rids)
                            logger.debug(f"Deleted batch of {len(rids)} records from {type_name}")
                    
                except Exception as batch_error:
                    logger.error(f"Batch deletion failed for {type_name}: {batch_error}")
                    break
                    
            return total_deleted
            
        except Exception as e:
            raise TransactionException(
                f"Safe delete all failed for type {type_name}",
                session_id=session_id
            ) from e

    def safe_bulk_operation(self, operation_func, *args, max_retries: int = 3, 
                           retry_delay: float = 1.0, **kwargs):
        """
        Execute a bulk operation with retry logic for transient errors.
        
        Parameters:
        - operation_func: The function to execute (e.g., bulk_insert, bulk_upsert)
        - args: Positional arguments for the operation function
        - max_retries: Maximum number of retry attempts
        - retry_delay: Delay between retries in seconds
        - kwargs: Keyword arguments for the operation function
        
        Returns:
        The result of the operation function
        
        Raises:
        The last exception if all retries fail
        """
        import time
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation_func(*args, **kwargs)
                
            except (TransactionException, BulkOperationException) as e:
                last_exception = e
                
                if attempt < max_retries:
                    # Check if this is a retryable error
                    if (isinstance(e, TransactionException) and e.is_idempotent_error) or \
                       (isinstance(e, BulkOperationException) and e.failed_records < e.total_records):
                        
                        logger.warning(f"Bulk operation attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                        continue
                
                # Not retryable or max retries reached
                break
                
            except Exception as e:
                # Non-retryable exception
                last_exception = e
                break
        
        # All retries failed
        raise last_exception

    def get_transaction_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get the status of a transaction.
        
        Parameters:
        - session_id (str): The session ID of the transaction
        
        Returns:
        Dict: Transaction status information
        
        Raises:
        TransactionException: If unable to get transaction status
        """
        try:
            # This is a hypothetical endpoint - actual implementation depends on ArcadeDB API
            result = self.query("sql", "SELECT * FROM sys:transactions WHERE session_id = ?", 
                              params=[session_id], session_id=session_id)
            
            if result and isinstance(result, list) and len(result) > 0:
                return result[0]
            else:
                return {"session_id": session_id, "status": "unknown"}
                
        except Exception as e:
            raise TransactionException(
                f"Failed to get transaction status for session {session_id}",
                session_id=session_id
            ) from e

    def get_records(self, type_names: Union[str, List[str]], 
                   where_clause: Optional[str] = None, 
                   limit: Optional[int] = None,
                   session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get records from one or more types with better query parsing.
        
        This method handles complex queries that might fail with UNION syntax
        by using alternative approaches.
        
        Parameters:
        - type_names: Single type name or list of type names to query
        - where_clause: Optional WHERE clause to filter results
        - limit: Optional limit on number of results
        - session_id: Optional session ID for transaction context
        
        Returns:
        List[Dict]: List of matching records
        
        Raises:
        QueryParsingException: If query parsing fails
        ValidationException: If parameters are invalid
        """
        if isinstance(type_names, str):
            type_names = [type_names]
            
        if not type_names or not all(isinstance(name, str) for name in type_names):
            raise ValidationException("Type names must be a string or list of strings")
            
        try:
            if len(type_names) == 1:
                # Single type query - straightforward
                query = f"SELECT * FROM {type_names[0]}"
                if where_clause:
                    query += f" WHERE {where_clause}"
                if limit:
                    query += f" LIMIT {limit}"
                    
                result = self.query("sql", query, session_id=session_id)
                return result if isinstance(result, list) else [result] if result else []
                
            else:
                # Multiple types - try different approaches
                all_results = []
                
                # Approach 1: Try UNION query
                try:
                    union_parts = []
                    for type_name in type_names:
                        part = f"SELECT * FROM {type_name}"
                        if where_clause:
                            part += f" WHERE {where_clause}"
                        union_parts.append(part)
                    
                    union_query = " UNION ".join(union_parts)
                    if limit:
                        union_query = f"SELECT * FROM ({union_query}) LIMIT {limit}"
                    
                    result = self.query("sql", union_query, session_id=session_id)
                    return result if isinstance(result, list) else [result] if result else []
                    
                except QueryParsingException:
                    logger.debug("UNION query failed, falling back to individual queries")
                    
                # Approach 2: Individual queries and merge results
                for type_name in type_names:
                    try:
                        query = f"SELECT * FROM {type_name}"
                        if where_clause:
                            query += f" WHERE {where_clause}"
                        # Distribute limit across types
                        if limit:
                            per_type_limit = max(1, limit // len(type_names))
                            query += f" LIMIT {per_type_limit}"
                            
                        result = self.query("sql", query, session_id=session_id)
                        if result:
                            if isinstance(result, list):
                                all_results.extend(result)
                            else:
                                all_results.append(result)
                                
                    except Exception as e:
                        logger.warning(f"Query failed for type {type_name}: {e}")
                        continue
                
                # Apply final limit if specified
                if limit and len(all_results) > limit:
                    all_results = all_results[:limit]
                    
                return all_results
                
        except Exception as e:
            raise QueryParsingException(
                f"Failed to get records from types {type_names}",
                query=f"get_records({type_names}, where={where_clause}, limit={limit})"
            ) from e

    def get_triplets(self, subject_types: Optional[List[str]] = None,
                    relation_types: Optional[List[str]] = None,
                    object_types: Optional[List[str]] = None,
                    limit: Optional[int] = None,
                    session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get graph triplets (subject-relation-object) with better query handling.
        
        This method handles graph traversal queries that might fail with
        standard MATCH syntax by using alternative approaches.
        
        Parameters:
        - subject_types: Optional list of subject vertex types to filter
        - relation_types: Optional list of edge types to filter  
        - object_types: Optional list of object vertex types to filter
        - limit: Optional limit on number of results
        - session_id: Optional session ID for transaction context
        
        Returns:
        List[Dict]: List of triplet records with subject, relation, and object
        
        Raises:
        QueryParsingException: If query parsing fails
        """
        try:
            # Approach 1: Try MATCH query syntax
            try:
                match_query = "MATCH {class: V, as: subject}-{class: E, as: relation}-{class: V, as: object}"
                
                # Add type filters
                conditions = []
                if subject_types:
                    subject_filter = " OR ".join([f"subject.@class = '{t}'" for t in subject_types])
                    conditions.append(f"({subject_filter})")
                    
                if relation_types:
                    relation_filter = " OR ".join([f"relation.@class = '{t}'" for t in relation_types])
                    conditions.append(f"({relation_filter})")
                    
                if object_types:
                    object_filter = " OR ".join([f"object.@class = '{t}'" for t in object_types])
                    conditions.append(f"({object_filter})")
                
                if conditions:
                    match_query += " WHERE " + " AND ".join(conditions)
                    
                match_query += " RETURN subject, relation, object"
                
                if limit:
                    match_query += f" LIMIT {limit}"
                
                result = self.query("sql", match_query, session_id=session_id)
                return result if isinstance(result, list) else [result] if result else []
                
            except QueryParsingException:
                logger.debug("MATCH query failed, falling back to edge traversal")
                
            # Approach 2: Use edge traversal
            try:
                # Get all edges and their connected vertices
                edge_query = "SELECT *, in() as subject, out() as object FROM E"
                
                # Add edge type filter
                if relation_types:
                    edge_filter = " OR ".join([f"@class = '{t}'" for t in relation_types])
                    edge_query += f" WHERE ({edge_filter})"
                    
                if limit:
                    edge_query += f" LIMIT {limit}"
                
                edges = self.query("sql", edge_query, session_id=session_id)
                
                if not edges:
                    return []
                    
                # Process results to match expected format
                triplets = []
                for edge in edges if isinstance(edges, list) else [edges]:
                    if not isinstance(edge, dict):
                        continue
                        
                    subject = edge.get('subject')
                    relation = {k: v for k, v in edge.items() if k not in ['subject', 'object']}
                    obj = edge.get('object')
                    
                    # Apply type filters
                    if subject_types and subject and subject.get('@class') not in subject_types:
                        continue
                    if object_types and obj and obj.get('@class') not in object_types:
                        continue
                        
                    triplets.append({
                        'subject': subject,
                        'relation': relation,
                        'object': obj
                    })
                
                return triplets
                
            except Exception as e:
                logger.debug(f"Edge traversal failed: {e}")
                
            # Approach 3: Query each edge type directly (avoids relying on base 'E' type)
            all_edges = []
            edge_types_to_query = relation_types if relation_types else []
            if edge_types_to_query:
                for et in edge_types_to_query:
                    try:
                        q = f"SELECT * FROM {et}"
                        if limit:
                            q += f" LIMIT {limit}"
                        partial = self.query("sql", q, session_id=session_id)
                        if partial:
                            all_edges.extend(partial if isinstance(partial, list) else [partial])
                    except Exception:
                        continue
            else:
                # No relation types specified — best-effort query on base E type
                try:
                    q = "SELECT * FROM E"
                    if limit:
                        q += f" LIMIT {limit}"
                    partial = self.query("sql", q, session_id=session_id)
                    if partial:
                        all_edges.extend(partial if isinstance(partial, list) else [partial])
                except Exception:
                    pass

            edges = all_edges
            
            # Return edges in triplet format (without full vertex data)
            triplets = []
            for edge in edges if isinstance(edges, list) else [edges]:
                if isinstance(edge, dict):
                    triplets.append({
                        'subject': {'@rid': edge.get('in', edge.get('@in'))},
                        'relation': edge,
                        'object': {'@rid': edge.get('out', edge.get('@out'))}
                    })
            
            return triplets
            
        except Exception as e:
            raise QueryParsingException(
                f"Failed to get triplets",
                query=f"get_triplets(subjects={subject_types}, relations={relation_types}, objects={object_types})"
            ) from e

    def bulk_insert(self, type_name: str, records: List[Dict[str, Any]], 
                   batch_size: int = 1000, session_id: Optional[str] = None) -> int:
        """
        Perform bulk insert operations.
        
        Parameters:
        - type_name (str): The type/table name to insert into
        - records (List[Dict]): List of records to insert
        - batch_size (int): Number of records to process in each batch (default: 1000)
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        int: Number of records successfully inserted
        
        Raises:
        BulkOperationException: If bulk operation fails
        """
        if not records:
            return 0
            
        if not isinstance(records, list):
            raise ValidationException("Records must be a list of dictionaries")
            
        total_inserted = 0
        total_failed = 0
        
        # Process records in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_failed = 0
            
            try:
                # Build INSERT statements for the batch
                insert_statements = []
                for record in batch:
                    if not isinstance(record, dict):
                        batch_failed += 1
                        continue
                        
                    # Build property assignments
                    properties = []
                    for key, value in record.items():
                        if isinstance(value, str):
                            escaped_value = value.replace("'", "\\'")
                            properties.append(f"{key} = '{escaped_value}'")
                        elif isinstance(value, (list, dict)):
                            # Handle JSON data
                            json_value = json.dumps(value).replace("'", "\\'")
                            properties.append(f"{key} = '{json_value}'")
                        else:
                            properties.append(f"{key} = {value}")
                    
                    if properties:
                        prop_str = ", ".join(properties)
                        insert_statements.append(f"INSERT INTO {type_name} SET {prop_str}")
                
                if insert_statements:
                    batch_query = "; ".join(insert_statements)
                    self.query("sqlscript", batch_query, session_id=session_id, is_command=True)
                
                batch_success = len(batch) - batch_failed
                total_inserted += batch_success
                total_failed += batch_failed
                    
            except Exception as e:
                total_failed += len(batch)
                raise BulkOperationException(
                    f"Bulk insert failed for type {type_name}",
                    failed_records=total_failed,
                    total_records=len(records)
                ) from e
        
        if total_failed > 0:
            raise BulkOperationException(
                f"Bulk insert partially failed for type {type_name}",
                failed_records=total_failed,
                total_records=len(records)
            )
            
        return total_inserted

    def bulk_upsert(self, type_name: str, records: List[Dict[str, Any]], 
                   key_field: str, batch_size: int = 1000, 
                   session_id: Optional[str] = None) -> int:
        """
        Perform bulk upsert (insert or update) operations.
        
        Parameters:
        - type_name (str): The type/table name to upsert into
        - records (List[Dict]): List of records to upsert
        - key_field (str): The field to use as the unique key for upsert
        - batch_size (int): Number of records to process in each batch (default: 1000)
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        int: Number of records successfully upserted
        
        Raises:
        BulkOperationException: If bulk operation fails
        """
        if not records:
            return 0
            
        if not isinstance(records, list):
            raise ValidationException("Records must be a list of dictionaries")
            
        if not key_field:
            raise ValidationException("Key field is required for upsert operations")
            
        total_upserted = 0
        total_failed = 0
        
        # Process records in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_failed = 0
            
            try:
                # Build UPSERT statements for the batch
                upsert_statements = []
                for record in batch:
                    if not isinstance(record, dict) or key_field not in record:
                        batch_failed += 1
                        continue
                        
                    # Build property assignments
                    properties = []
                    key_value = record[key_field]

                    for key, value in record.items():
                        if isinstance(value, str):
                            escaped_value = value.replace("'", "\\'")
                            properties.append(f"{key} = '{escaped_value}'")
                        elif isinstance(value, (list, dict)):
                            # Handle JSON data
                            json_value = json.dumps(value).replace("'", "\\'")
                            properties.append(f"{key} = '{json_value}'")
                        else:
                            properties.append(f"{key} = {value}")
                    
                    if properties:
                        prop_str = ", ".join(properties)
                        if isinstance(key_value, str):
                            escaped_key = key_value.replace("'", "\\'")
                            key_condition = f"{key_field} = '{escaped_key}'"
                        else:
                            key_condition = f"{key_field} = {key_value}"

                        upsert_statements.append(f"UPDATE {type_name} SET {prop_str} UPSERT WHERE {key_condition}")
                
                if upsert_statements:
                    batch_query = "; ".join(upsert_statements)
                    self.query("sqlscript", batch_query, session_id=session_id, is_command=True)
                
                batch_success = len(batch) - batch_failed
                total_upserted += batch_success
                total_failed += batch_failed
                    
            except Exception as e:
                total_failed += len(batch)
                raise BulkOperationException(
                    f"Bulk upsert failed for type {type_name}",
                    failed_records=total_failed,
                    total_records=len(records)
                ) from e
        
        if total_failed > 0:
            raise BulkOperationException(
                f"Bulk upsert partially failed for type {type_name}",
                failed_records=total_failed,
                total_records=len(records)
            )
            
        return total_upserted

    def bulk_delete(self, type_name: str, conditions: List[str], 
                   batch_size: int = 1000, session_id: Optional[str] = None, 
                   safe_mode: bool = True) -> int:
        """
        Perform bulk delete operations.
        
        Parameters:
        - type_name (str): The type/table name to delete from
        - conditions (List[str]): List of WHERE conditions for deletion
        - batch_size (int): Number of conditions to process in each batch (default: 1000)
        - session_id (str): Optional session ID for transaction context
        - safe_mode (bool): If True, prevents deletion of all records without conditions
        
        Returns:
        int: Number of records successfully deleted (approximate)
        
        Raises:
        BulkOperationException: If bulk operation fails
        ValidationException: If attempting unsafe bulk delete
        """
        if not conditions:
            if safe_mode:
                raise ValidationException(
                    "Bulk delete without conditions is not allowed in safe mode. "
                    "Set safe_mode=False to delete all records."
                )
            else:
                # Delete all records - use TRUNCATE if possible
                try:
                    result = self.query("sql", f"TRUNCATE TYPE {type_name} UNSAFE", 
                                      session_id=session_id, is_command=True)
                    return 0  # TRUNCATE doesn't return count
                except Exception:
                    # Fallback to DELETE FROM
                    result = self.query("sql", f"DELETE FROM {type_name}", 
                                      session_id=session_id, is_command=True)
                    return 0  # DELETE FROM doesn't return count reliably
            
        if not isinstance(conditions, list):
            raise ValidationException("Conditions must be a list of strings")
            
        total_deleted = 0
        total_failed = 0
        
        # Process conditions in batches
        for i in range(0, len(conditions), batch_size):
            batch = conditions[i:i + batch_size]
            batch_failed = 0
            
            try:
                # Build DELETE statements for the batch
                delete_statements = []
                for condition in batch:
                    if not isinstance(condition, str):
                        batch_failed += 1
                        continue
                        
                    delete_statements.append(f"DELETE FROM {type_name} WHERE {condition}")
                
                if delete_statements:
                    batch_query = "; ".join(delete_statements)
                    self.query("sqlscript", batch_query, session_id=session_id, is_command=True)
                
                batch_success = len(batch) - batch_failed
                total_deleted += batch_success
                total_failed += batch_failed
                    
            except Exception as e:
                total_failed += len(batch)
                raise BulkOperationException(
                    f"Bulk delete failed for type {type_name}",
                    failed_records=total_failed,
                    total_records=len(conditions)
                ) from e
        
        if total_failed > 0:
            raise BulkOperationException(
                f"Bulk delete partially failed for type {type_name}",
                failed_records=total_failed,
                total_records=len(conditions)
            )
            
        return total_deleted

    def execute_batch(self, queries: List[str], session_id: Optional[str] = None) -> List[Any]:
        """
        Execute multiple queries in a batch.
        
        Parameters:
        - queries (List[str]): List of SQL queries to execute
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        List[Any]: Results from each query
        
        Raises:
        ValidationException: If queries list is invalid
        """
        if not queries or not isinstance(queries, list):
            raise ValidationException("Queries must be a non-empty list of strings")
            
        results = []
        for query in queries:
            if not isinstance(query, str):
                raise ValidationException("All queries must be strings")
                
            try:
                result = self.query("sql", query, session_id=session_id, is_command=True)
                results.append(result)
            except Exception as e:
                # Include the failing query in the error
                if hasattr(e, 'query'):
                    e.query = query
                raise
                
        return results

    def execute_transaction(self, queries: List[str], 
                          isolation_level: IsolationLevel = IsolationLevel.READ_COMMITTED) -> List[Any]:
        """
        Execute multiple queries within a single transaction.
        
        Parameters:
        - queries (List[str]): List of SQL queries to execute
        - isolation_level (IsolationLevel): Transaction isolation level
        
        Returns:
        List[Any]: Results from each query
        
        Raises:
        TransactionException: If transaction fails
        ValidationException: If queries list is invalid
        """
        if not queries or not isinstance(queries, list):
            raise ValidationException("Queries must be a non-empty list of strings")
            
        session_id = None
        try:
            # Begin transaction
            session_id = self.begin_transaction(isolation_level)
            
            # Execute all queries in the transaction
            results = self.execute_batch(queries, session_id=session_id)
            
            # Commit transaction
            self.commit_transaction(session_id)
            
            return results
            
        except Exception as e:
            # Rollback transaction on any error
            if session_id:
                try:
                    self.rollback_transaction(session_id)
                except Exception as rollback_error:
                    # Log rollback error but don't mask the original error
                    logger.error(f"Failed to rollback transaction {session_id}: {rollback_error}")
            
            raise TransactionException(
                f"Transaction failed: {str(e)}",
                session_id=session_id
            ) from e

    def vector_search(self, type_name: str, embedding_field: str, 
                     query_embedding: List[float], top_k: int = 10,
                     where_clause: Optional[str] = None,
                     session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search.
        
        Parameters:
        - type_name (str): The type/table name to search in
        - embedding_field (str): The field containing the vector embeddings
        - query_embedding (List[float]): The query vector to search for
        - top_k (int): Number of most similar results to return (default: 10)
        - where_clause (str): Optional WHERE clause to filter results
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        List[Dict]: List of similar records with similarity scores
        
        Raises:
        VectorOperationException: If vector search fails
        ValidationException: If parameters are invalid
        """
        if not isinstance(query_embedding, list) or not query_embedding:
            raise ValidationException("Query embedding must be a non-empty list of floats")
            
        if not all(isinstance(x, (int, float)) for x in query_embedding):
            raise ValidationException("Query embedding must contain only numeric values")
            
        if top_k <= 0:
            raise ValidationException("top_k must be a positive integer")
            
        try:
            embedding_json = json.dumps(query_embedding)

            # Use the SELECT form of vectorNeighbors which returns an array of
            # {record, distance} objects. distance=0 means exact match (closest),
            # so a WHERE-clause threshold would wrongly exclude exact matches.
            index_name = f"{type_name}[{embedding_field}]"
            base_query = (
                f"SELECT vectorNeighbors('{index_name}', {embedding_json}, {top_k})"
                f" AS neighbors FROM {type_name} LIMIT 1"
            )

            raw = self.query("sql", base_query, session_id=session_id)

            if not raw or not isinstance(raw, list):
                return []

            neighbors = raw[0].get("neighbors", []) if raw[0] else []
            if not isinstance(neighbors, list):
                return []

            results = []
            for nb in neighbors:
                if not isinstance(nb, dict):
                    continue
                record = nb.get("record", {})
                if where_clause:
                    # Re-fetch the record applying the WHERE filter
                    rid = record.get("@rid", "")
                    if not rid:
                        continue
                    try:
                        check = self.query(
                            "sql",
                            f"SELECT * FROM {type_name} WHERE @rid = '{rid}' AND ({where_clause})",
                            session_id=session_id,
                        )
                        if not check:
                            continue
                    except Exception:
                        continue
                results.append(record)

            return results

        except Exception as e:
            raise VectorOperationException(
                f"Vector search failed for type {type_name}",
                dimensions=len(query_embedding)
            ) from e

    def create_vector_index(self, type_name: str, property_name: str, 
                           dimensions: int, index_type: str = "HNSW",
                           session_id: Optional[str] = None) -> bool:
        """
        Create a vector index for similarity search optimization.
        
        Parameters:
        - type_name (str): The type/table name
        - property_name (str): The property containing vector embeddings
        - dimensions (int): The dimensionality of the vectors
        - index_type (str): The type of vector index (default: "HNSW")
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        bool: True if index was created successfully
        
        Raises:
        VectorOperationException: If index creation fails
        ValidationException: If parameters are invalid
        """
        if dimensions <= 0:
            raise ValidationException("Dimensions must be a positive integer")
            
        if not property_name or not isinstance(property_name, str):
            raise ValidationException("Property name must be a non-empty string")
            
        try:
            # LSMVectorIndex syntax introduced with JVector 4.0 (ArcadeDB latest)
            similarity = "COSINE" if index_type.upper() in ("HNSW", "LSM_VECTOR", "COSINE") else index_type.upper()
            create_query = (
                f"CREATE INDEX ON {type_name} ({property_name}) LSM_VECTOR METADATA {{"
                f" dimensions: {dimensions},"
                f" similarity: '{similarity}'"
                f" }}"
            )
            result = self.query("sql", create_query, session_id=session_id, is_command=True)
            logger.info(f"Created LSM_VECTOR index on {type_name}.{property_name} "
                        f"(dimensions={dimensions}, similarity={similarity})")
            return True

        except Exception as e:
            raise VectorOperationException(
                f"Failed to create vector index on {type_name}.{property_name}",
                dimensions=dimensions
            ) from e

    def get_vector_similarity(self, type_name: str, embedding_field: str,
                             record_id: str, query_embedding: List[float],
                             similarity_function: str = "cosine_similarity",
                             session_id: Optional[str] = None) -> float:
        """
        Calculate similarity between a query vector and a specific record's vector.
        
        Parameters:
        - type_name (str): The type/table name
        - embedding_field (str): The field containing the vector embedding
        - record_id (str): The ID of the record to compare against
        - query_embedding (List[float]): The query vector
        - similarity_function (str): The similarity function to use (default: "cosine_similarity")
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        float: The similarity score
        
        Raises:
        VectorOperationException: If similarity calculation fails
        ValidationException: If parameters are invalid
        """
        if not isinstance(query_embedding, list) or not query_embedding:
            raise ValidationException("Query embedding must be a non-empty list of floats")
            
        if not all(isinstance(x, (int, float)) for x in query_embedding):
            raise ValidationException("Query embedding must contain only numeric values")
            
        try:
            embedding_json = json.dumps(query_embedding)

            # Map legacy/generic names to the ArcadeDB SQL vector functions
            _func_map = {
                "cosine_similarity": "vectorCosineSimilarity",
                "dot_product": "vectorDotProduct",
                "euclidean": "vectorL2Distance",
                "l2": "vectorL2Distance",
            }
            func = _func_map.get(similarity_function.lower(), similarity_function)

            query = (
                f"SELECT {func}({embedding_field}, {embedding_json}) AS similarity"
                f" FROM {type_name}"
                f" WHERE @rid = '{record_id}'"
            )

            result = self.query("sql", query, session_id=session_id)

            if result and isinstance(result, list) and len(result) > 0:
                return float(result[0].get('similarity', 0.0))
            return 0.0

        except Exception as e:
            raise VectorOperationException(
                f"Failed to calculate vector similarity for record {record_id}",
                dimensions=len(query_embedding)
            ) from e

    def batch_vector_search(self, searches: List[Dict[str, Any]], 
                           session_id: Optional[str] = None) -> List[List[Dict[str, Any]]]:
        """
        Perform multiple vector searches in a batch.
        
        Parameters:
        - searches (List[Dict]): List of search configurations, each containing:
            - type_name (str): The type/table name to search in
            - embedding_field (str): The field containing vector embeddings
            - query_embedding (List[float]): The query vector
            - top_k (int): Number of results to return (optional, default: 10)
            - where_clause (str): Optional WHERE clause (optional)
        - session_id (str): Optional session ID for transaction context
        
        Returns:
        List[List[Dict]]: Results for each search query
        
        Raises:
        VectorOperationException: If batch search fails
        ValidationException: If parameters are invalid
        """
        if not searches or not isinstance(searches, list):
            raise ValidationException("Searches must be a non-empty list of search configurations")
            
        results = []
        failed_searches = 0
        
        for i, search_config in enumerate(searches):
            if not isinstance(search_config, dict):
                raise ValidationException(f"Search configuration {i} must be a dictionary")
                
            required_fields = ['type_name', 'embedding_field', 'query_embedding']
            for field in required_fields:
                if field not in search_config:
                    raise ValidationException(f"Search configuration {i} missing required field: {field}")
            
            try:
                search_result = self.vector_search(
                    type_name=search_config['type_name'],
                    embedding_field=search_config['embedding_field'],
                    query_embedding=search_config['query_embedding'],
                    top_k=search_config.get('top_k', 10),
                    where_clause=search_config.get('where_clause'),
                    session_id=session_id
                )
                results.append(search_result)
                
            except Exception as e:
                failed_searches += 1
                logger.error(f"Vector search {i} failed: {e}")
                results.append([])  # Empty result for failed search
                
        if failed_searches == len(searches):
            raise VectorOperationException("All vector searches in batch failed")
            
        return results

    def __repr__(self) -> str:
        """
        Return a string representation of the DatabaseDao instance.

        Returns:
        str: A string representation of the form "<DatabaseDao database_name={self.database_name}> @ {self.client}".
        """
        return f"<DatabaseDao database_name={self.database_name}> @ {self.client}"
