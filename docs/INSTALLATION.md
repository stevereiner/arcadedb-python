# Installing Enhanced ArcadeDB Python Driver from Local Source

## 🚀 **Installation Methods**

### **Method 1: Direct pip install from local directory**

```bash
# Navigate to the arcadedb-python directory
cd C:\newdev3\arcadedb-python

# Install in development mode (editable install)
pip install -e .

# Or install normally from local source
pip install .
```

### **Method 2: Using uv (recommended)**

```bash
# Navigate to the arcadedb-python directory
cd C:\newdev3\arcadedb-python

# Install with uv in development mode
uv pip install -e .

# Or install normally with uv
uv pip install .
```

### **Method 3: Install from local wheel**

```bash
# First build the wheel
cd C:\newdev3\arcadedb-python
uv build

# Install from the built wheel
pip install dist/arcadedb_python-0.3.0-py3-none-any.whl

# Or with uv
uv pip install dist/arcadedb_python-0.3.0-py3-none-any.whl
```

### **Method 4: Install in another project**

If you want to install this enhanced version in another project (like arcadedb-llama-index):

```bash
# From the other project directory
cd C:\newdev3\arcadedb-llama-index

# Install from local path
pip install -e C:\newdev3\arcadedb-python

# Or with uv
uv pip install -e C:\newdev3\arcadedb-python
```

## 📋 **Installation Options Explained**

### **Development Mode (`-e` flag)**
- **Editable Install:** Changes to source code are immediately reflected
- **Best for:** Development, testing, debugging
- **Command:** `pip install -e .` or `uv pip install -e .`

### **Regular Install**
- **Standard Install:** Copies files to site-packages
- **Best for:** Production deployment
- **Command:** `pip install .` or `uv pip install .`

### **Wheel Install**
- **Pre-built Package:** Install from built wheel file
- **Best for:** Distribution, deployment
- **Command:** `pip install dist/arcadedb_python-0.2.0-py3-none-any.whl`

## 🔧 **Verification Steps**

After installation, verify the enhanced features are available:

```python
# Test import
import arcadedb_python
print(f"Version: {arcadedb_python.__version__}")

# Test enhanced exceptions
from arcadedb_python import (
    ArcadeDBException,
    QueryParsingException, 
    TransactionException,
    BulkOperationException,
    VectorOperationException
)

# Test enhanced DatabaseDao
from arcadedb_python import DatabaseDao, SyncClient

# Create client and database instance
client = SyncClient("localhost", "2480", username="root", password="test")
db = DatabaseDao(client, "test_db")

# Verify new methods are available
print("Enhanced methods available:")
print(f"- bulk_insert: {hasattr(db, 'bulk_insert')}")
print(f"- bulk_upsert: {hasattr(db, 'bulk_upsert')}")
print(f"- vector_search: {hasattr(db, 'vector_search')}")
print(f"- get_records: {hasattr(db, 'get_records')}")
print(f"- get_triplets: {hasattr(db, 'get_triplets')}")
print(f"- safe_delete_all: {hasattr(db, 'safe_delete_all')}")
```

## 🧪 **Running Tests After Installation**

```bash
# Run all tests
uv run pytest

# Run only enhanced feature tests
uv run pytest tests/test_enhanced_features.py -v

# Run with coverage
uv run pytest --cov=arcadedb_python tests/
```

## 📦 **Dependencies**

The enhanced driver includes these dependencies:

### **Core Dependencies:**
```toml
dependencies = [
    "requests>=2.25.0",
    "retry>=0.9.2",
]
```

### **Optional Dependencies:**
```toml
[project.optional-dependencies]
postgresql = ["psycopg>=3.0.0"]
cypher = ["pygments>=2.0.0"] 
full = ["psycopg>=3.0.0", "pygments>=2.0.0"]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0", 
    "pytest-mock>=3.10.0",
    # ... other dev dependencies
]
```

### **Install with Optional Dependencies:**
```bash
# Install with PostgreSQL support
pip install -e ".[postgresql]"

# Install with Cypher support  
pip install -e ".[cypher]"

# Install with all optional features
pip install -e ".[full]"

# Install with development tools
pip install -e ".[dev]"
```

## 🔄 **Updating from Previous Version**

If you have an older version installed:

```bash
# Uninstall old version
pip uninstall arcadedb-python

# Install enhanced version
pip install -e C:\newdev3\arcadedb-python

# Or with uv
uv pip uninstall arcadedb-python
uv pip install -e C:\newdev3\arcadedb-python
```

## 🌐 **For LlamaIndex Integration**

To use the enhanced driver with LlamaIndex:

```bash
# Navigate to your LlamaIndex project
cd C:\newdev3\arcadedb-llama-index

# Install the enhanced driver
uv pip install -e C:\newdev3\arcadedb-python

# Verify installation
python -c "import arcadedb_python; print('Enhanced driver installed successfully')"

# Run LlamaIndex tests to verify compatibility
pytest tests/ -v
```

## 📋 **Troubleshooting**

### **Common Issues:**

1. **Import Errors:**
   ```bash
   # Ensure you're in the right environment
   which python
   pip list | grep arcadedb
   ```

2. **Version Conflicts:**
   ```bash
   # Check for multiple installations
   pip show arcadedb-python
   
   # Clean install
   pip uninstall arcadedb-python
   pip install -e .
   ```

3. **Permission Issues:**
   ```bash
   # Use --user flag if needed
   pip install --user -e .
   ```

## ✅ **Success Indicators**

After successful installation, you should see:

- ✅ All 28 enhanced feature tests pass
- ✅ New exception classes are importable
- ✅ New DatabaseDao methods are available
- ✅ LlamaIndex integration tests improve significantly
- ✅ No import or dependency conflicts

---

*This enhanced version addresses all critical issues identified in the LlamaIndex integration and provides significant performance and reliability improvements.*
