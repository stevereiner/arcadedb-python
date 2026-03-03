# Logging

Every module in `arcadedb_python` uses a named logger derived from its module
path (`logging.getLogger(__name__)`), so Python's standard logging hierarchy
gives you fine-grained control over what gets emitted and where.

## Logger names

| Short alias | Full logger name | Covers |
|---|---|---|
| `package` | `arcadedb_python` | entire package (parent of all below) |
| `api` | `arcadedb_python.api` | all API modules |
| `api.client` | `arcadedb_python.api.client` | base client (headers, URL building) |
| `api.sync` | `arcadedb_python.api.sync` | HTTP requests and responses |
| `dao` | `arcadedb_python.dao` | all DAO modules |
| `dao.database` | `arcadedb_python.dao.database` | database operations, transactions, vectors |

Setting a level on a parent logger (e.g. `arcadedb_python`) applies to all
children unless a child has its own level set.

## Quick reference

### One-call setup

```python
from arcadedb_python import configure_logging
import logging

configure_logging(level=logging.DEBUG)  # accepts int or string "DEBUG"
```

### Quiet by default, verbose for one module

```python
from arcadedb_python import configure_logging

configure_logging(
    level="WARNING",
    module_levels={
        "arcadedb_python.api.sync": "DEBUG",  # full HTTP traffic
    },
)
```

Short aliases from `LOGGER_NAMES` work too:

```python
configure_logging(
    level="WARNING",
    module_levels={"api.sync": "DEBUG"},
)
```

### Only errors, except INFO from the DAO

```python
from arcadedb_python import configure_logging
import logging

configure_logging(
    level=logging.ERROR,
    module_levels={"dao.database": logging.INFO},
)
```

### Log to a file instead of stderr

```python
import logging
from arcadedb_python import configure_logging

configure_logging(
    level="DEBUG",
    handler=logging.FileHandler("arcadedb.log"),
)
```

### Prevent output from appearing in your root logger

```python
from arcadedb_python import configure_logging

configure_logging(level="WARNING", propagate=False)
```

## Direct control (no helper needed)

Useful inside frameworks (Django, FastAPI, etc.) that manage logging
configuration themselves:

```python
import logging

logging.getLogger("arcadedb_python").setLevel(logging.WARNING)
logging.getLogger("arcadedb_python.api.sync").setLevel(logging.DEBUG)
logging.getLogger("arcadedb_python.dao.database").setLevel(logging.INFO)
```

## dictConfig (production apps)

```python
import logging.config

LOGGING = {
    "version": 1,
    "loggers": {
        "arcadedb_python": {"level": "WARNING"},
        "arcadedb_python.api.sync": {"level": "DEBUG"},
    },
}
logging.config.dictConfig(LOGGING)
```

## Discovering logger names at runtime

```python
from arcadedb_python import LOGGER_NAMES

print(LOGGER_NAMES)
# {
#   'package':      'arcadedb_python',
#   'api':          'arcadedb_python.api',
#   'api.client':   'arcadedb_python.api.client',
#   'api.sync':     'arcadedb_python.api.sync',
#   'dao':          'arcadedb_python.dao',
#   'dao.database': 'arcadedb_python.dao.database',
# }
```

## `configure_logging` reference

```python
configure_logging(
    level="WARNING",          # default level for the whole package
    module_levels={...},      # per-module overrides (optional)
    handler=None,             # custom handler; StreamHandler used if omitted
    fmt="...",                # log record format string
    datefmt="...",            # date/time format string
    propagate=True,           # whether to propagate to the root logger
)
```

`configure_logging` is a convenience helper for scripts and simple
applications. For anything that already manages its own logging configuration,
use `logging.getLogger("arcadedb_python.<subpath>")` directly.
