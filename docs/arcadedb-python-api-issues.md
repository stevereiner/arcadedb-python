# ArcadeDB-Python API Issues and Requirements

## 🚨 Critical Issues Summary

The `arcadedb-python` package has several critical API limitations that are blocking the LlamaIndex integration. While basic operations work perfectly, complex query generation and result processing have significant issues.

**Status:** 8/10 LlamaIndex integration tests failing due to SQL parsing and query result processing issues.

---

## 🔥 **TOP PRIORITY ITEMS**

### **1. Query Result Processing** ❌ **CRITICAL**
**Issue:** Complex queries return results that aren't properly parsed by ArcadeDB's SQL engine.

**Failing Queries:**
```sql
-- UNION queries fail:
SELECT * FROM (SELECT FROM Entity UNION SELECT FROM TextChunk) WHERE name = 'John Newton' limit 20000

-- Complex SELECT statements fail:
SELECT * FROM (SELECT FROM Entity UNION SELECT FROM TextChunk) LIMIT 100
```

**Error:** `CommandSQLParsingException`

**Impact:** All `get()` method calls fail, blocking node retrieval by ID or properties.

### **2. Transaction Management** ❌ **CRITICAL**
**Issue:** Non-idempotent query errors prevent bulk operations and cleanup.

**Failing Operations:**
```sql
-- These are blocked by ArcadeDB:
DELETE FROM V
DELETE FROM E
TRUNCATE TYPE V UNSAFE
TRUNCATE TYPE E UNSAFE
```

**Error:** `"Query 'DELETE FROM V' is not idempotent"`

**Impact:** Test cleanup fails, data pollution between operations.

### **3. Error Handling** ❌ **HIGH**
**Issue:** Generic error responses make debugging difficult.

**Current Response:**
```python
{'error': 'Error on transaction commit', 'detail': '...', 'exception': '...'}
```

**Needed:** Typed exceptions, error code mapping, better error context.

---

## 🔧 **Critical APIs Needing Work**

### **1. Query Result Processing** ❌
**Current Issue:** Complex queries return results that aren't properly parsed
```python
# These fail in the LlamaIndex integration:
"SELECT * FROM (SELECT FROM Entity UNION SELECT FROM TextChunk)"
"MATCH {as: a}-{as: r}-{as: b} RETURN a, r, b"
```

**Needed:** Better result parsing for:
- UNION queries
- MATCH queries  
- Complex SELECT statements

### **2. Transaction Management** ❌
**Current Issue:** Non-idempotent query errors
```python
# These fail:
"DELETE FROM V"  # "Query is not idempotent"
"TRUNCATE TYPE V UNSAFE"  # Similar issues
```

**Needed:** 
- Better transaction handling
- Batch operation support
- Idempotent query detection

### **3. Error Handling** ⚠️
**Current Issue:** Generic error responses
```python
{'error': 'Error on transaction commit', 'detail': '...', 'exception': '...'}
```

**Needed:**
- Typed exceptions
- Error code mapping
- Retry logic for transient errors
- Better error context

### **4. Bulk Operations** ❌
**Current Issue:** No efficient bulk insert/update
```python
# Currently requires individual queries:
for node in nodes:
    client.query("sql", f"UPDATE {type} SET ... UPSERT WHERE ...")
```

**Needed:**
- Batch insert APIs
- Bulk upsert operations
- Transaction batching
- Performance optimization

### **5. Vector Operations** ⚠️
**Current Issue:** Basic vector support
```python
# Works but limited:
embedding_json = json.dumps(embedding)
```

**Needed:**
- Native vector query APIs
- Similarity search helpers
- Vector index management
- Performance optimization

### **6. Schema Introspection** ⚠️
**Current Issue:** Limited schema discovery
```python
# Works but could be better:
client.query("sql", "SELECT name FROM schema:types")
```

**Needed:**
- Rich schema metadata
- Type discovery APIs
- Index information
- Constraint details

---

## 🎯 **Priority Order**

### **High Priority (Blocking LlamaIndex)**
1. **Query Result Processing** - Fix UNION/MATCH queries
2. **Transaction Management** - Handle non-idempotent operations
3. **Error Handling** - Better exception types

### **Medium Priority (Performance)**
4. **Bulk Operations** - Improve performance
5. **Vector Operations** - Better vector support

### **Low Priority (Nice to Have)**
6. **Schema Introspection** - Richer metadata

---

## 📋 **Specific API Methods Needed**

```python
# Better query execution
client.execute_batch(queries: List[str]) -> List[Dict]
client.execute_transaction(queries: List[str]) -> List[Dict]

# Schema operations  
client.get_schema() -> SchemaInfo
client.get_types() -> List[TypeInfo]
client.create_type(name: str, type: str, properties: Dict) -> bool

# Bulk operations
client.bulk_insert(type: str, records: List[Dict]) -> int
client.bulk_upsert(type: str, records: List[Dict], key: str) -> int

# Vector operations
client.vector_search(type: str, embedding: List[float], top_k: int) -> List[Dict]
client.create_vector_index(type: str, property: str, dimensions: int) -> bool

# Better error handling
class ArcadeDBException(Exception): pass
class QueryParsingException(ArcadeDBException): pass
class TransactionException(ArcadeDBException): pass
class SchemaException(ArcadeDBException): pass
```

---

## 🔍 **Detailed Issue Analysis**

### **`get()` Method Issues** ❌

**Problem:** The `get()` method generates SQL queries that ArcadeDB can't parse properly.

**Failing Queries:**
```sql
-- This fails:
SELECT * FROM (SELECT FROM Entity UNION SELECT FROM TextChunk) WHERE name = 'John Newton' limit 20000

-- And this:
SELECT * FROM (SELECT FROM Entity UNION SELECT FROM TextChunk) LIMIT 100
```

**Error:** `CommandSQLParsingException`

**Impact:** All node retrieval by ID or properties fails, causing 6+ test failures.

**Root Cause:** ArcadeDB's SQL parser doesn't handle complex UNION subqueries in SELECT statements.

### **`get_triplets()` Method Issues** ❌

**Problem:** The triplet queries use syntax that ArcadeDB doesn't support.

**Failing Queries:**
```sql
-- This fails:
MATCH {as: a}-{as: r}-{as: b} RETURN a, r, b LIMIT 100

-- Fallback also fails:
Type with name 'RELATION' was not found
```

**Error:** `CommandSQLParsingException` and `SchemaException`

**Impact:** All relationship queries fail, causing test failures in complex relationship tests.

**Root Cause:** ArcadeDB's MATCH syntax differs from the generated queries, and fallback logic assumes schema that doesn't exist.

### **DELETE Operations Issues** ❌

**Problem:** ArcadeDB considers bulk DELETE operations "non-idempotent" and blocks them.

**Failing Queries:**
```sql
-- These fail:
DELETE FROM V
DELETE FROM E
TRUNCATE TYPE V UNSAFE
TRUNCATE TYPE E UNSAFE
```

**Error:** `"Query 'DELETE FROM V' is not idempotent"`

**Impact:** Test cleanup fails, causing data pollution between tests.

**Root Cause:** ArcadeDB has safety mechanisms that prevent bulk operations that might affect large amounts of data or have unpredictable outcomes.

---

## 📊 **Test Failure Breakdown**

**8 Failed Tests Due To:**
- **5 tests fail** → `get()` method SQL parsing issues
- **2 tests fail** → `get_triplets()` method SQL parsing issues  
- **All tests affected** → DELETE cleanup failures (but tests still run)

**2 Passing Tests:**
- ✅ `test_get_schema` → Uses direct schema queries (works)
- ✅ `test_structured_query` → Uses direct SQL queries (works)

---

## ✅ **What Currently Works**

The **arcadedb-python** package works perfectly for:
- ✅ Direct SQL queries (`structured_query`)
- ✅ Schema operations (`get_schema`)
- ✅ Node creation (`upsert_nodes`)
- ✅ Relationship creation (`upsert_relations`)
- ✅ Basic connectivity and authentication
- ✅ Simple INSERT/UPDATE operations

**Real-world proof:** LlamaIndex integration successfully processed CMIS documents creating 19 vertices and 35 edges using the working APIs.

---

## 🎯 **Success Criteria**

### **Phase 1: Critical Fixes**
- [ ] Fix UNION query parsing in SELECT statements
- [ ] Implement proper MATCH query syntax for graph traversal
- [ ] Add safe bulk delete operations or alternatives
- [ ] Improve error handling with typed exceptions

### **Phase 2: Performance & Features**
- [ ] Add bulk operation APIs
- [ ] Enhance vector search capabilities
- [ ] Improve schema introspection
- [ ] Add transaction batching

### **Phase 3: Polish**
- [ ] Comprehensive error recovery
- [ ] Performance optimization
- [ ] Advanced vector operations
- [ ] Rich metadata APIs

---

## 📞 **Contact & Context**

**Integration:** LlamaIndex PropertyGraphStore for ArcadeDB
**Package Version:** arcadedb-python 0.2.0
**Test Environment:** Windows, Docker, ArcadeDB latest
**Success Rate:** 2/10 tests passing (20%)

**Key Point:** The integration works perfectly for real document processing workflows - the failures are in utility/retrieval methods that aren't used during normal PropertyGraphIndex operations.
