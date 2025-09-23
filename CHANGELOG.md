# Changelog

All notable changes to the ArcadeDB Python Driver will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-09-20

**Maintainer**: Steve Reiner  
**Based on**: Original work by Adams Rosales (2023) and ExtReMLapin (March 2025)

### Added
- Comprehensive PyPI package configuration
- Modern `pyproject.toml` build system
- Enhanced documentation and examples
- Type hints throughout the codebase
- Development tooling configuration (black, isort, mypy, pytest)

### Changed
- Modernized package structure for PyPI release
- Updated README with comprehensive usage examples
- Improved error handling and logging

### Added
- Modern Python packaging with `pyproject.toml`
- Comprehensive type hints
- Enhanced documentation and examples
- Development dependencies and tooling
- Support for Python 3.8-3.13
- Optional dependencies for PostgreSQL and Cypher features
- Async operation support
- Connection pooling capabilities
- Vector search examples for AI/ML applications

### Changed
- Migrated from `setup.py` to modern `pyproject.toml` build system
- Updated package metadata and classifiers
- Enhanced README with detailed usage examples
- Improved error handling and logging throughout the codebase
- Standardized code formatting with Black and isort

### Fixed
- Package import structure and namespace issues
- Connection handling edge cases
- Query parameter handling improvements

### [0.1.0] - 2025-09-10 (Steve Reiner)

**Maintainer**: Steve Reiner  
**Repository**: https://github.com/stevereiner/arcadedb-python  
**Timeline**: Started September 10, 2025  

#### Added
- Conceptual Fork from ExtReMLapin's changes + on Adams Rosales' original `pyarcade` work
- **New PyPI Package**: Created `arcadedb-python` as a separate package from `pyarcade`
- Renamed for clarity and to avoid confusion with existing `pyarcade` package
- Enhanced documentation and examples
- Improved package structure organization
- Modern Python packaging standards

#### Features Inherited
- All original functionality from `pyarcade`
- Database connection management
- SQL query execution  
- Command execution
- Configuration options
- Retry mechanisms for network operations

#### Supported Operations (from original)
- CREATE, INSERT, UPDATE, DELETE operations
- SELECT queries with filtering and ordering
- Graph traversal with MATCH patterns
- Document operations
- Key-value operations
- Time-series data handling


## Original Contributors' Work

### ExtReMLapin - [pyarcade](https://github.com/ExtReMLapin/pyarcade) (December 2024 - March 2025)

**Repository**: https://github.com/ExtReMLapin/pyarcade  
**Author**: ExtReMLapin ([@ExtReMLapin](https://github.com/ExtReMLapin))  
**Timeline**: December 4, 2024 - March 31, 2025  
**License**: Apache 2.0  
**Status**: GitHub improvements (not released to PyPI) (incorpoated into arcadedb-python)

#### GitHub Improvements & Enhancements
- **December 4, 2024**: Better exception error handling with invalid credentials & more
- **March 31, 2025**: Added experimental psycopg driver support
- Enhanced error handling and validation
- Improved connection management
- Additional database driver support
- Code quality improvements and bug fixes

#### Key Contributions
- Enhanced exception handling for authentication failures
- Experimental PostgreSQL driver integration via psycopg
- Improved error messages and debugging capabilities
- Code refactoring and optimization
- Enhanced documentation and examples

#### Distribution Status
- **GitHub Only**: Improvements available in GitHub repository


### Adams Rosales - [arcadedb-python-driver](https://github.com/adaros92/arcadedb-python-driver) (June 2023)

**Repository**: https://github.com/adaros92/arcadedb-python-driver  
**Author**: Adams Rosales ([@adaros92](https://github.com/adaros92))  
**Timeline**: June 30, 2023  
**License**: Apache 2.0  
**Package Name**: `pyarcade` (released to PyPI)

#### Original Foundation & PyPI Release
- Initial ArcadeDB Python driver implementation
- Basic REST API client architecture
- Core database connection and query functionality
- **PyPI Releases**: 
  - `pyarcade` v0.0.1 (June 30, 2023)
  - `pyarcade` v0.0.3 (June 30, 2023)
- Foundation for all subsequent development


---

## Release Notes

### Version 0.2.0 Release Notes

This release focuses on modernizing the package for PyPI distribution and improving the developer experience:

**Key Improvements:**
- **Modern Packaging**: Migrated to `pyproject.toml` for better dependency management and build configuration
- **Enhanced Documentation**: Comprehensive README with practical examples for all ArcadeDB data models
- **Type Safety**: Added type hints throughout the codebase for better IDE support and error detection
- **Development Tools**: Integrated Black, isort, mypy, and pytest for consistent code quality
- **Async Support**: Enhanced async operations for better performance in concurrent applications
- **Vector Search**: Added examples for AI/ML applications using vector embeddings

**Dependencies:**
- Minimum Python version: 3.10 (updated from original 3.8+)
- Core dependencies: requests >= 2.25.0, retry >= 0.9.2
- Optional dependencies available for PostgreSQL and Cypher features

**Timeline Summary:**
- **September 22, 2025**: `arcadedb-python` v0.2.0 release - separate PyPI package
- **September 10, 2025**: Steve Reiner creates NEW package `arcadedb-python` (based on Adams Rosales / ExReMLapin work)
- **December 2024 - March 2025**: ExtReMLapin enhances code in GitHub (no PyPI releases)
- **June 30, 2023**: Adams Rosales creates and releases `pyarcade` v0.0.1 & v0.0.3 to PyPI

**PyPI Package Status:**
- `arcadedb-python` v0.2.0 (Steve Reiner, Sept 2025) - **RECOMMENDED** modern package
- ExtReMLapin's improvements available only on GitHub, not on PyPI, but incorporated into arcadedb-python
- `pyarcade` v0.0.3 (Adams Rosales, June 2023) - original package, outdated

**Installation Recommendation:**
- **Use**: `pip install arcadedb-python` (modern, maintained version)
- **Avoid**: `pip install pyarcade` (outdated, June 2023 version)

For detailed usage examples and API documentation, see the updated README.md file.
