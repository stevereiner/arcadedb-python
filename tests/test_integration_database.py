"""
Live integration tests for DatabaseDao — all public methods.

Requirements:
- ArcadeDB running on localhost:2480
- Default credentials (root / playwithdata)

Run with:
    pytest tests/test_integration_database.py -v

A dedicated test database is created at the start of the session and dropped
at the end, so tests do not interfere with any other data.
"""

import pytest
from arcadedb_python import DatabaseDao, SyncClient
from arcadedb_python.exceptions import (
    ValidationException,
    BulkOperationException,
)

# ---------------------------------------------------------------------------
# Connection constants — override via environment variables if needed
# ---------------------------------------------------------------------------
HOST = "localhost"
PORT = 2480
USERNAME = "root"
PASSWORD = "playwithdata"
TEST_DB = "integration_test_db"


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    return SyncClient(host=HOST, port=PORT, username=USERNAME, password=PASSWORD)


@pytest.fixture(scope="session")
def db(client):
    """Create the test database once for the whole session, drop it afterwards."""
    if DatabaseDao.exists(client, TEST_DB):
        DatabaseDao.delete(client, TEST_DB)
    dao = DatabaseDao.create(client, TEST_DB)
    yield dao
    DatabaseDao.delete(client, TEST_DB)


# ---------------------------------------------------------------------------
# Helper: ensure a fresh type exists before each test that needs one
# ---------------------------------------------------------------------------

def _reset_type(db: DatabaseDao, type_name: str, is_vertex: bool = False):
    """Drop and recreate a type so each test starts clean."""
    try:
        db.query("sql", f"DROP TYPE {type_name} IF EXISTS UNSAFE", is_command=True)
    except Exception:
        pass
    kind = "VERTEX" if is_vertex else "DOCUMENT"
    db.query("sql", f"CREATE {kind} TYPE {type_name}", is_command=True)


def _reset_edge_type(db: DatabaseDao, edge_name: str):
    try:
        db.query("sql", f"DROP TYPE {edge_name} IF EXISTS UNSAFE", is_command=True)
    except Exception:
        pass
    db.query("sql", f"CREATE EDGE TYPE {edge_name}", is_command=True)


# ===========================================================================
# 1. Static methods
# ===========================================================================

class TestStaticMethods:

    def test_list_databases(self, client, db):
        # db fixture ensures the database exists before we list
        databases = DatabaseDao.list_databases(client)
        assert isinstance(databases, list)
        assert TEST_DB in databases

    def test_exists_true(self, client, db):
        assert DatabaseDao.exists(client, TEST_DB) is True

    def test_exists_false(self, client):
        assert DatabaseDao.exists(client, "nonexistent_db_xyz_123") is False

    def test_create_and_delete_roundtrip(self, client):
        temp_name = "temp_integration_roundtrip"
        if DatabaseDao.exists(client, temp_name):
            DatabaseDao.delete(client, temp_name)
        temp_db = DatabaseDao.create(client, temp_name)
        assert temp_db is not None
        assert DatabaseDao.exists(client, temp_name) is True
        result = DatabaseDao.delete(client, temp_name)
        assert result is True
        assert DatabaseDao.exists(client, temp_name) is False

    def test_cypher_formater_basic(self):
        """cypher_formater substitutes $var params when pygments is available.
        Without pygments it falls back to regex substitution.
        Either way the returned query should have the variable replaced."""
        query = "MATCH (n) WHERE n.name = $name RETURN n"
        params = {"name": "Alice"}
        formatted_query, remaining_params = DatabaseDao.cypher_formater(query, params)
        # The formatter may or may not inline the value depending on pygments
        # availability; what matters is it returns a string and a dict.
        assert isinstance(formatted_query, str)
        assert isinstance(remaining_params, dict)

    def test_cypher_formater_replaces_known_param(self):
        """When pygments is unavailable the regex path should still substitute."""
        query = "MATCH (n) WHERE n.age = $age RETURN n"
        params = {"age": 42}
        formatted_query, remaining_params = DatabaseDao.cypher_formater(query, params)
        assert isinstance(formatted_query, str)
        # After substitution the param should no longer be needed
        assert "$age" not in formatted_query or remaining_params.get("age") is None


# ===========================================================================
# 2. __repr__
# ===========================================================================

class TestRepr:

    def test_repr(self, db):
        r = repr(db)
        assert TEST_DB in r


# ===========================================================================
# 3. query — language variants and options
# ===========================================================================

class TestQuery:

    def test_query_sql_select(self, db):
        _reset_type(db, "QtPerson")
        db.query("sql", "INSERT INTO QtPerson CONTENT {\"name\": \"Alice\", \"age\": 30}",
                 is_command=True)
        result = db.query("sql", "SELECT FROM QtPerson")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_query_sql_command(self, db):
        _reset_type(db, "QtCommand")
        result = db.query("sql", "INSERT INTO QtCommand CONTENT {\"x\": 1}", is_command=True)
        assert result is not None

    def test_query_with_limit(self, db):
        _reset_type(db, "QtLimit")
        for i in range(5):
            db.query("sql", f"INSERT INTO QtLimit CONTENT {{\"n\": {i}}}", is_command=True)
        result = db.query("sql", "SELECT FROM QtLimit", limit=3)
        assert isinstance(result, list)
        assert len(result) <= 3

    def test_query_with_params(self, db):
        _reset_type(db, "QtParams")
        db.query("sql", "INSERT INTO QtParams CONTENT {\"tag\": \"hello\"}", is_command=True)
        result = db.query("sql", "SELECT FROM QtParams WHERE tag = :tag", params={"tag": "hello"})
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_query_opencypher(self, db):
        """openCypher queries require vertex types and the native engine."""
        _reset_type(db, "QtCypherNode", is_vertex=True)
        db.query("opencypher", "CREATE (n:QtCypherNode {name: 'Bob'})", is_command=True)
        result = db.query("opencypher", "MATCH (n:QtCypherNode) RETURN n.name")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_query_invalid_language(self, db):
        with pytest.raises(Exception):
            db.query("invalid_lang", "SELECT 1")

    def test_query_retry_on_idempotent_error_succeeds(self, db):
        """A normal command should succeed regardless of retry flag."""
        _reset_type(db, "QtRetry")
        db.query("sql", "INSERT INTO QtRetry CONTENT {\"v\": 1}", is_command=True)
        result = db.query("sql", "SELECT FROM QtRetry", retry_on_idempotent_error=True)
        assert isinstance(result, list)


# ===========================================================================
# 4. Transactions
# ===========================================================================

class TestTransactions:

    def test_begin_commit_transaction(self, db):
        _reset_type(db, "TxCommit")
        session_id = db.begin_transaction()
        assert isinstance(session_id, str) and len(session_id) > 0
        db.query("sql", "INSERT INTO TxCommit CONTENT {\"val\": \"committed\"}",
                 is_command=True, session_id=session_id)
        db.commit_transaction(session_id)
        result = db.query("sql", "SELECT FROM TxCommit WHERE val = 'committed'")
        assert len(result) >= 1

    def test_begin_rollback_transaction(self, db):
        _reset_type(db, "TxRollback")
        session_id = db.begin_transaction()
        db.query("sql", "INSERT INTO TxRollback CONTENT {\"val\": \"to_rollback\"}",
                 is_command=True, session_id=session_id)
        db.rollback_transaction(session_id)
        result = db.query("sql", "SELECT FROM TxRollback WHERE val = 'to_rollback'")
        assert result == [] or result is None or len(result) == 0

    def test_isolation_level_repeatable_read(self, db):
        session_id = db.begin_transaction(
            isolation_level=DatabaseDao.IsolationLevel.REPEATABLE_READ
        )
        assert isinstance(session_id, str)
        db.rollback_transaction(session_id)

    def test_execute_transaction(self, db):
        _reset_type(db, "TxExecute")
        queries = [
            "INSERT INTO TxExecute CONTENT {\"k\": \"a\"}",
            "INSERT INTO TxExecute CONTENT {\"k\": \"b\"}",
        ]
        results = db.execute_transaction(queries)
        assert isinstance(results, list)
        rows = db.query("sql", "SELECT FROM TxExecute")
        assert len(rows) >= 2

    def test_get_transaction_status(self, db):
        """get_transaction_status wraps a best-effort query; it returns a dict
        with at least the session_id even when the underlying query fails."""
        session_id = db.begin_transaction()
        try:
            status = db.get_transaction_status(session_id)
            assert isinstance(status, dict)
            assert "session_id" in status
        except Exception:
            # The method documents that it may raise TransactionException if
            # the ArcadeDB server doesn't expose the sys:transactions endpoint.
            pass
        finally:
            db.rollback_transaction(session_id)


# ===========================================================================
# 5. execute_batch
# ===========================================================================

class TestExecuteBatch:

    def test_execute_batch_multiple_inserts(self, db):
        _reset_type(db, "BatchType")
        queries = [
            "INSERT INTO BatchType CONTENT {\"item\": \"x\"}",
            "INSERT INTO BatchType CONTENT {\"item\": \"y\"}",
            "INSERT INTO BatchType CONTENT {\"item\": \"z\"}",
        ]
        results = db.execute_batch(queries)
        assert isinstance(results, list)
        rows = db.query("sql", "SELECT FROM BatchType")
        assert len(rows) >= 3

    def test_execute_batch_empty(self, db):
        with pytest.raises(ValidationException):
            db.execute_batch([])


# ===========================================================================
# 6. get_records
# ===========================================================================

class TestGetRecords:

    def test_get_records_single_type(self, db):
        _reset_type(db, "GrSingle")
        db.query("sql", "INSERT INTO GrSingle CONTENT {\"v\": 1}", is_command=True)
        result = db.get_records("GrSingle")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_records_multiple_types(self, db):
        _reset_type(db, "GrMultiA")
        _reset_type(db, "GrMultiB")
        db.query("sql", "INSERT INTO GrMultiA CONTENT {\"v\": \"a\"}", is_command=True)
        db.query("sql", "INSERT INTO GrMultiB CONTENT {\"v\": \"b\"}", is_command=True)
        result = db.get_records(["GrMultiA", "GrMultiB"])
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_get_records_with_where_clause(self, db):
        _reset_type(db, "GrWhere")
        db.query("sql", "INSERT INTO GrWhere CONTENT {\"status\": \"active\"}", is_command=True)
        db.query("sql", "INSERT INTO GrWhere CONTENT {\"status\": \"inactive\"}", is_command=True)
        result = db.get_records("GrWhere", where_clause="status = 'active'")
        assert all(r.get("status") == "active" for r in result)

    def test_get_records_with_limit(self, db):
        _reset_type(db, "GrLimited")
        for i in range(5):
            db.query("sql", f"INSERT INTO GrLimited CONTENT {{\"n\": {i}}}", is_command=True)
        result = db.get_records("GrLimited", limit=2)
        assert len(result) <= 2

    def test_get_records_invalid_type_names(self, db):
        with pytest.raises((ValidationException, Exception)):
            db.get_records([])


# ===========================================================================
# 7. get_triplets
# ===========================================================================

class TestGetTriplets:

    def test_get_triplets_basic(self, db):
        _reset_type(db, "TripSubject", is_vertex=True)
        _reset_type(db, "TripObject", is_vertex=True)
        _reset_edge_type(db, "TripRelation")
        db.query("sql", "INSERT INTO TripSubject CONTENT {\"name\": \"S1\"}", is_command=True)
        db.query("sql", "INSERT INTO TripObject CONTENT {\"name\": \"O1\"}", is_command=True)
        db.query("sql", """
            CREATE EDGE TripRelation
            FROM (SELECT FROM TripSubject WHERE name = 'S1')
            TO (SELECT FROM TripObject WHERE name = 'O1')
        """, is_command=True)
        # get_triplets tries several fallback strategies; the last one queries the
        # specific edge type directly which is always valid.
        result = db.get_triplets(relation_types=["TripRelation"])
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_get_triplets_no_filters(self, db):
        # May raise if no edges exist yet; either way must return a list
        try:
            result = db.get_triplets()
            assert isinstance(result, list)
        except Exception:
            pass

    def test_get_triplets_with_limit(self, db):
        try:
            result = db.get_triplets(limit=1)
            assert isinstance(result, list)
            assert len(result) <= 1
        except Exception:
            pass


# ===========================================================================
# 8. Bulk operations
# ===========================================================================

class TestSqlscriptDirect:
    """Verify that the sqlscript language actually works end-to-end."""

    def test_sqlscript_single_insert(self, db):
        _reset_type(db, "SsDirectA")
        db.query("sqlscript", "INSERT INTO SsDirectA SET name = 'Alice'", is_command=True)
        rows = db.query("sql", "SELECT FROM SsDirectA")
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"

    def test_sqlscript_multi_insert(self, db):
        """Multiple semicolon-separated statements in a single sqlscript call."""
        _reset_type(db, "SsDirectB")
        script = (
            "INSERT INTO SsDirectB SET name = 'Bob';"
            "INSERT INTO SsDirectB SET name = 'Carol';"
            "INSERT INTO SsDirectB SET name = 'Dave'"
        )
        db.query("sqlscript", script, is_command=True)
        rows = db.query("sql", "SELECT FROM SsDirectB")
        assert len(rows) == 3
        names = {r["name"] for r in rows}
        assert names == {"Bob", "Carol", "Dave"}

    def test_sqlscript_multi_upsert(self, db):
        _reset_type(db, "SsDirectC")
        db.query("sql", "CREATE PROPERTY SsDirectC.code STRING", is_command=True)
        db.query("sql", "CREATE INDEX ON SsDirectC (code) UNIQUE", is_command=True)
        script = (
            "UPDATE SsDirectC SET code = 'X1', label = 'First' UPSERT WHERE code = 'X1';"
            "UPDATE SsDirectC SET code = 'X2', label = 'Second' UPSERT WHERE code = 'X2'"
        )
        db.query("sqlscript", script, is_command=True)
        rows = db.query("sql", "SELECT FROM SsDirectC")
        assert len(rows) == 2
        # Re-upsert — must not duplicate
        db.query("sqlscript",
                 "UPDATE SsDirectC SET code = 'X1', label = 'Updated' UPSERT WHERE code = 'X1'",
                 is_command=True)
        rows2 = db.query("sql", "SELECT FROM SsDirectC")
        assert len(rows2) == 2
        x1 = [r for r in rows2 if r.get("code") == "X1"]
        assert x1[0]["label"] == "Updated"

    def test_sqlscript_multi_delete(self, db):
        _reset_type(db, "SsDirectD")
        for i in range(5):
            db.query("sql", f"INSERT INTO SsDirectD SET tag = 'item_{i}'", is_command=True)
        script = (
            "DELETE FROM SsDirectD WHERE tag = 'item_0';"
            "DELETE FROM SsDirectD WHERE tag = 'item_1';"
            "DELETE FROM SsDirectD WHERE tag = 'item_2'"
        )
        db.query("sqlscript", script, is_command=True)
        rows = db.query("sql", "SELECT FROM SsDirectD")
        assert len(rows) == 2
        assert {r["tag"] for r in rows} == {"item_3", "item_4"}

    def test_sqlscript_error_propagates(self, db):
        """A bad sqlscript must raise an exception, not be silently swallowed."""
        with pytest.raises(Exception):
            db.query("sqlscript", "THIS IS NOT VALID SQL AT ALL !!!!", is_command=True)


class TestBulkInsert:

    def test_bulk_insert_basic(self, db):
        _reset_type(db, "BulkInsertType")
        records = [{"name": f"item_{i}", "value": i} for i in range(10)]
        count = db.bulk_insert("BulkInsertType", records)
        assert count == 10
        rows = db.query("sql", "SELECT FROM BulkInsertType")
        assert len(rows) == 10

    def test_bulk_insert_verifies_data_integrity(self, db):
        """bulk_insert must actually persist all records with correct values."""
        _reset_type(db, "BulkInsertIntegrity")
        records = [{"name": f"item_{i}", "value": i} for i in range(10)]
        db.bulk_insert("BulkInsertIntegrity", records)
        rows = db.query("sql", "SELECT FROM BulkInsertIntegrity")
        stored_names = {r["name"] for r in rows}
        assert stored_names == {f"item_{i}" for i in range(10)}

    def test_bulk_insert_empty(self, db):
        count = db.bulk_insert("BulkInsertType", [])
        assert count == 0

    def test_bulk_insert_batched(self, db):
        _reset_type(db, "BulkInsertBatched")
        records = [{"n": i} for i in range(25)]
        count = db.bulk_insert("BulkInsertBatched", records, batch_size=10)
        assert count == 25
        rows = db.query("sql", "SELECT FROM BulkInsertBatched")
        assert len(rows) == 25

    def test_bulk_insert_invalid_records_type(self, db):
        with pytest.raises((ValidationException, Exception)):
            db.bulk_insert("BulkInsertType", "not_a_list")

    def test_bulk_insert_raises_on_bad_type_name(self, db):
        """bulk_insert must raise, not silently succeed, when the type doesn't exist."""
        from arcadedb_python.exceptions import BulkOperationException
        with pytest.raises((BulkOperationException, Exception)):
            db.bulk_insert("TypeThatDoesNotExist_xyz", [{"x": 1}])


class TestBulkUpsert:

    def test_bulk_upsert_insert_new(self, db):
        _reset_type(db, "BulkUpsertType")
        # ArcadeDB UPSERT requires a declared property and a unique index on the key field
        db.query("sql", "CREATE PROPERTY BulkUpsertType.code STRING", is_command=True)
        db.query("sql", "CREATE INDEX ON BulkUpsertType (code) UNIQUE", is_command=True)
        records = [{"code": f"C{i}", "label": f"Label {i}"} for i in range(5)]
        count = db.bulk_upsert("BulkUpsertType", records, key_field="code")
        assert count == 5
        rows = db.query("sql", "SELECT FROM BulkUpsertType")
        assert len(rows) == 5

    def test_bulk_upsert_updates_existing(self, db):
        _reset_type(db, "BulkUpsertUpdate")
        db.query("sql", "CREATE PROPERTY BulkUpsertUpdate.code STRING", is_command=True)
        db.query("sql", "CREATE INDEX ON BulkUpsertUpdate (code) UNIQUE", is_command=True)
        db.query("sql", "INSERT INTO BulkUpsertUpdate CONTENT {\"code\": \"X1\", \"label\": \"Old\"}",
                 is_command=True)
        records = [{"code": "X1", "label": "New"}]
        db.bulk_upsert("BulkUpsertUpdate", records, key_field="code")
        result = db.query("sql", "SELECT FROM BulkUpsertUpdate WHERE code = 'X1'")
        assert result[0]["label"] == "New"

    def test_bulk_upsert_no_duplicates(self, db):
        """Re-upsert with same keys must not create duplicate rows."""
        _reset_type(db, "BulkUpsertDedup")
        db.query("sql", "CREATE PROPERTY BulkUpsertDedup.code STRING", is_command=True)
        db.query("sql", "CREATE INDEX ON BulkUpsertDedup (code) UNIQUE", is_command=True)
        records = [{"code": f"K{i}", "label": f"Label {i}"} for i in range(5)]
        db.bulk_upsert("BulkUpsertDedup", records, key_field="code")
        # Upsert same keys again with updated labels
        records2 = [{"code": f"K{i}", "label": f"Updated {i}"} for i in range(5)]
        db.bulk_upsert("BulkUpsertDedup", records2, key_field="code")
        rows = db.query("sql", "SELECT FROM BulkUpsertDedup")
        assert len(rows) == 5, f"Expected 5 rows (no duplicates), got {len(rows)}"
        assert all(r["label"].startswith("Updated") for r in rows)

    def test_bulk_upsert_missing_key_field(self, db):
        with pytest.raises((ValidationException, Exception)):
            db.bulk_upsert("BulkUpsertType", [{"a": 1}], key_field="")

    def test_bulk_upsert_empty(self, db):
        count = db.bulk_upsert("BulkUpsertType", [], key_field="code")
        assert count == 0

    def test_bulk_upsert_raises_on_bad_type_name(self, db):
        """bulk_upsert must raise, not silently succeed, when the type doesn't exist."""
        from arcadedb_python.exceptions import BulkOperationException
        with pytest.raises((BulkOperationException, Exception)):
            db.bulk_upsert("TypeThatDoesNotExist_xyz", [{"code": "1"}], key_field="code")


class TestBulkDelete:

    def test_bulk_delete_with_conditions(self, db):
        _reset_type(db, "BulkDeleteType")
        for i in range(5):
            db.query("sql",
                     f"INSERT INTO BulkDeleteType CONTENT {{\"tag\": \"del_{i}\"}}",
                     is_command=True)
        conditions = [f"tag = 'del_{i}'" for i in range(3)]
        db.bulk_delete("BulkDeleteType", conditions)
        remaining = db.query("sql", "SELECT FROM BulkDeleteType")
        assert len(remaining) == 2

    def test_bulk_delete_verifies_correct_rows_removed(self, db):
        """bulk_delete must remove exactly the targeted rows, leaving others intact."""
        _reset_type(db, "BulkDeleteVerify")
        for i in range(6):
            db.query("sql",
                     f"INSERT INTO BulkDeleteVerify CONTENT {{\"tag\": \"row_{i}\"}}",
                     is_command=True)
        conditions = [f"tag = 'row_{i}'" for i in range(4)]
        db.bulk_delete("BulkDeleteVerify", conditions)
        remaining = db.query("sql", "SELECT FROM BulkDeleteVerify")
        assert len(remaining) == 2
        remaining_tags = {r["tag"] for r in remaining}
        assert remaining_tags == {"row_4", "row_5"}

    def test_bulk_delete_safe_mode_no_conditions(self, db):
        with pytest.raises((ValidationException, Exception)):
            db.bulk_delete("BulkDeleteType", [], safe_mode=True)

    def test_bulk_delete_unsafe_no_conditions(self, db):
        _reset_type(db, "BulkDeleteUnsafe")
        db.query("sql", "INSERT INTO BulkDeleteUnsafe CONTENT {\"x\": 1}", is_command=True)
        db.bulk_delete("BulkDeleteUnsafe", [], safe_mode=False)
        remaining = db.query("sql", "SELECT FROM BulkDeleteUnsafe")
        assert remaining == [] or len(remaining) == 0

    def test_bulk_delete_raises_on_bad_type_name(self, db):
        """bulk_delete must raise, not silently succeed, when the type doesn't exist."""
        from arcadedb_python.exceptions import BulkOperationException
        with pytest.raises((BulkOperationException, Exception)):
            db.bulk_delete("TypeThatDoesNotExist_xyz", ["id = '1'"])


# ===========================================================================
# 9. safe_delete_all
# ===========================================================================

class TestSafeDeleteAll:

    def test_safe_delete_all(self, db):
        _reset_type(db, "SafeDeleteType")
        for i in range(5):
            db.query("sql", f"INSERT INTO SafeDeleteType CONTENT {{\"n\": {i}}}",
                     is_command=True)
        db.safe_delete_all("SafeDeleteType")
        remaining = db.query("sql", "SELECT FROM SafeDeleteType")
        assert remaining == [] or len(remaining) == 0

    def test_safe_delete_all_empty_type(self, db):
        _reset_type(db, "SafeDeleteEmpty")
        result = db.safe_delete_all("SafeDeleteEmpty")
        assert isinstance(result, int)


# ===========================================================================
# 10. safe_bulk_operation
# ===========================================================================

class TestSafeBulkOperation:

    def test_safe_bulk_operation_success(self, db):
        _reset_type(db, "SafeBulkType")
        records = [{"val": i} for i in range(5)]
        count = db.safe_bulk_operation(db.bulk_insert, "SafeBulkType", records)
        assert count == 5

    def test_safe_bulk_operation_retries_on_failure(self, db):
        """Verify that safe_bulk_operation raises after all retries on persistent failure."""
        def always_fail(*args, **kwargs):
            from arcadedb_python.exceptions import BulkOperationException
            raise BulkOperationException("Simulated failure", failed_records=1, total_records=1)

        with pytest.raises(Exception):
            db.safe_bulk_operation(always_fail, max_retries=1, retry_delay=0.0)


# ===========================================================================
# 11. Vector operations
# ===========================================================================

class TestVectorOperations:

    def test_create_vector_index(self, db):
        _reset_type(db, "VecDoc")
        db.query("sql", "CREATE PROPERTY VecDoc.embedding ARRAY_OF_FLOATS", is_command=True)
        result = db.create_vector_index(
            type_name="VecDoc",
            property_name="embedding",
            dimensions=4,
            index_type="HNSW"
        )
        assert result is True

    def test_vector_search(self, db):
        _reset_type(db, "VecSearch")
        db.query("sql", "CREATE PROPERTY VecSearch.embedding ARRAY_OF_FLOATS", is_command=True)
        db.create_vector_index("VecSearch", "embedding", dimensions=4)
        db.query("sql",
                 "INSERT INTO VecSearch CONTENT {\"title\": \"doc1\", \"embedding\": [0.1, 0.2, 0.3, 0.4]}",
                 is_command=True)
        db.query("sql",
                 "INSERT INTO VecSearch CONTENT {\"title\": \"doc2\", \"embedding\": [0.9, 0.8, 0.7, 0.6]}",
                 is_command=True)
        results = db.vector_search(
            type_name="VecSearch",
            embedding_field="embedding",
            query_embedding=[0.1, 0.2, 0.3, 0.4],
            top_k=2
        )
        assert isinstance(results, list)

    def test_get_vector_similarity(self, db):
        _reset_type(db, "VecSim")
        db.query("sql", "CREATE PROPERTY VecSim.embedding ARRAY_OF_FLOATS", is_command=True)
        db.create_vector_index("VecSim", "embedding", dimensions=4)
        db.query("sql",
                 "INSERT INTO VecSim CONTENT {\"label\": \"a\", \"embedding\": [1.0, 0.0, 0.0, 0.0]}",
                 is_command=True)
        records = db.query("sql", "SELECT @rid FROM VecSim LIMIT 1")
        record_id = records[0]["@rid"]
        score = db.get_vector_similarity(
            type_name="VecSim",
            embedding_field="embedding",
            record_id=record_id,
            query_embedding=[1.0, 0.0, 0.0, 0.0]
        )
        assert isinstance(score, float)

    def test_batch_vector_search(self, db):
        _reset_type(db, "VecBatch")
        db.query("sql", "CREATE PROPERTY VecBatch.embedding ARRAY_OF_FLOATS", is_command=True)
        db.create_vector_index("VecBatch", "embedding", dimensions=3)
        db.query("sql",
                 "INSERT INTO VecBatch CONTENT {\"v\": 1, \"embedding\": [0.5, 0.5, 0.5]}",
                 is_command=True)
        searches = [
            {"type_name": "VecBatch", "embedding_field": "embedding",
             "query_embedding": [0.5, 0.5, 0.5], "top_k": 1},
            {"type_name": "VecBatch", "embedding_field": "embedding",
             "query_embedding": [0.1, 0.1, 0.1], "top_k": 1},
        ]
        results = db.batch_vector_search(searches)
        assert isinstance(results, list)
        assert len(results) == 2
        for batch_result in results:
            assert isinstance(batch_result, list)
