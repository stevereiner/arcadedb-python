"""Logging configuration helpers for arcadedb_python.

Each module in this package uses a named logger derived from its module path
(via ``logging.getLogger(__name__)``), so you can control verbosity at any
granularity supported by Python's logging hierarchy:

- ``arcadedb_python``            - the entire package
- ``arcadedb_python.api``        - all API modules
- ``arcadedb_python.api.client`` - only the base client
- ``arcadedb_python.api.sync``   - only the sync HTTP client
- ``arcadedb_python.dao``        - all DAO modules
- ``arcadedb_python.dao.database`` - only the database DAO

Use :func:`configure_logging` for a quick one-call setup, or manipulate the
loggers directly via ``logging.getLogger("arcadedb_python.<subpath>")`` for
full control.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Union

__all__ = ["configure_logging", "get_logger", "LOGGER_NAMES"]

# Canonical logger names exposed for discoverability
LOGGER_NAMES = {
    "package": "arcadedb_python",
    "api": "arcadedb_python.api",
    "api.client": "arcadedb_python.api.client",
    "api.sync": "arcadedb_python.api.sync",
    "dao": "arcadedb_python.dao",
    "dao.database": "arcadedb_python.dao.database",
}

_DEFAULT_FORMAT = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return the logger for a given module path.

    Args:
        name: A dotted module path such as ``"arcadedb_python.api.sync"`` or
              a short alias from :data:`LOGGER_NAMES` such as ``"api.sync"``.

    Returns:
        The corresponding :class:`logging.Logger` instance.
    """
    resolved = LOGGER_NAMES.get(name, name)
    return logging.getLogger(resolved)


def configure_logging(
    level: Union[int, str] = logging.WARNING,
    *,
    module_levels: Optional[Dict[str, Union[int, str]]] = None,
    handler: Optional[logging.Handler] = None,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATE_FORMAT,
    propagate: bool = True,
) -> None:
    """Configure logging for the arcadedb_python package.

    Sets a default level on the top-level ``arcadedb_python`` logger and
    optionally overrides individual sub-loggers.  A :class:`logging.StreamHandler`
    writing to *stderr* is attached to the package logger when no *handler* is
    provided and the logger has no handlers yet.

    Args:
        level: Default log level for the entire ``arcadedb_python`` package.
            Accepts an integer (e.g. ``logging.DEBUG``) or a string
            (e.g. ``"DEBUG"``).  Defaults to ``WARNING``.
        module_levels: Optional mapping of module paths (or short aliases from
            :data:`LOGGER_NAMES`) to log levels.  These override *level* for
            specific sub-loggers.  Example::

                configure_logging(
                    level="WARNING",
                    module_levels={
                        "arcadedb_python.api.sync": "DEBUG",
                        "dao.database": logging.INFO,
                    },
                )

        handler: A custom :class:`logging.Handler` to attach to the package
            logger.  When *None* a :class:`logging.StreamHandler` is used,
            but only if the package logger has no handlers already (avoids
            duplicate output when called multiple times).
        fmt: Log record format string.  Defaults to a timestamp + level +
            logger name + message format.
        datefmt: Date/time format string for the formatter.
        propagate: Whether the package logger should propagate records to the
            root logger.  Set to ``False`` to silence arcadedb_python output
            from appearing in the root handler.  Defaults to ``True``.

    Example - silence everything except errors from the DAO layer::

        from arcadedb_python import configure_logging
        import logging

        configure_logging(
            level=logging.ERROR,
            module_levels={"arcadedb_python.dao.database": logging.DEBUG},
        )

    Example - enable full debug output for the HTTP client only::

        configure_logging(
            level=logging.WARNING,
            module_levels={"api.sync": "DEBUG", "api.client": "DEBUG"},
        )
    """
    pkg_logger = logging.getLogger("arcadedb_python")
    pkg_logger.setLevel(_resolve_level(level))
    pkg_logger.propagate = propagate

    if handler is None:
        if not pkg_logger.handlers:
            _handler = logging.StreamHandler()
            _handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
            pkg_logger.addHandler(_handler)
    else:
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        pkg_logger.addHandler(handler)

    if module_levels:
        for path, lvl in module_levels.items():
            resolved = LOGGER_NAMES.get(path, path)
            logging.getLogger(resolved).setLevel(_resolve_level(lvl))


_LEVEL_NAMES: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
}


def _resolve_level(level: Union[int, str]) -> int:
    if isinstance(level, str):
        numeric = _LEVEL_NAMES.get(level.upper())
        if numeric is None:
            raise ValueError(
                f"Unknown log level {level!r}. "
                f"Valid names: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            )
        return numeric
    return level
