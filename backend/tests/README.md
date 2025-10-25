# Test Suite Documentation

## Overview
This directory contains comprehensive tests for the NLP Query Engine, including unit tests, integration tests, performance tests, and security tests.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── test_schema_service.py      # Schema service unit tests
├── test_integration.py         # Integration tests
├── test_performance.py         # Performance and load tests
├── test_security.py            # Security and vulnerability tests
├── test_runner.py              # Comprehensive test runner
└── README.md                   # This documentation
```

## Test Categories

### 1. Unit Tests (`test_schema_service.py`)
- **Purpose**: Test individual components in isolation
- **Coverage**: Schema discovery, natural language mapping, database operations
- **Execution**: `pytest tests/test_schema_service.py -v`

### 2. Integration Tests (`test_integration.py`)
- **Purpose**: Test component interactions and data flow
- **Coverage**: Database connections, document processing, query workflows
- **Execution**: `pytest tests/test_integration.py -v`

### 3. Performance Tests (`test_performance.py`)
- **Purpose**: Test system performance under various load conditions
- **Coverage**: Response times, throughput, memory usage, concurrent operations
- **Execution**: `pytest tests/test_performance.py -v`

### 4. Security Tests (`test_security.py`)
- **Purpose**: Test security vulnerabilities and prevention mechanisms
- **Coverage**: SQL injection, XSS, path traversal, input validation
- **Execution**: `pytest tests/test_security.py -v`

## Running Tests

### Run All Tests
```bash
# From backend directory
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/test_schema_service.py -v

# Integration tests only
pytest tests/test_integration.py -v

# Performance tests only
pytest tests/test_performance.py -v

# Security tests only
pytest tests/test_security.py -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=api --cov-report=html --cov-report=xml
```

### Run with Markers
```bash
# Fast tests only
pytest tests/ -v -m "fast"

# Slow tests only
pytest tests/ -v -m "slow"

# Database tests only
pytest tests/ -v -m "database"
```

## Test Configuration

### Environment Variables
Set these environment variables for testing:
```bash
export ENVIRONMENT=test
export DATABASE_URL=sqlite:///test.db
export REDIS_URL=redis://localhost:6379/1
export CHROMA_URL=http://localhost:8001
export MISTRAL_API_KEY=test_key
```

### Test Dependencies
Install test dependencies:
```bash
pip install pytest pytest-cov pytest-xdist safety bandit
```

## Test Fixtures

### Database Fixtures
- `test_db_manager`: Database manager instance
- `sample_database_schema`: Sample schema for testing
- `mock_database_connection`: Mock database connection

### Service Fixtures
- `test_redis_service`: Redis service instance
- `test_chromadb_service`: ChromaDB service instance
- `test_mistral_client`: Mistral client instance

### Data Fixtures
- `sample_documents`: Sample documents for testing
- `sample_queries`: Sample queries for testing
- `integration_test_data`: Integration test data

## Test Utilities

### TestRunner Class
The `TestRunner` class provides comprehensive test execution:
```python
from tests.test_runner import TestRunner

runner = TestRunner()
results = runner.run_all_tests()
```

### Test Utils
Utility functions for common test operations:
```python
from tests.conftest import TestUtils

utils = TestUtils()
document = utils.create_test_document("test.txt", "content", "resume")
query = utils.create_test_query("How many employees?", "SQL_QUERY")
```

## Performance Testing

### Benchmarks
- **Database Queries**: < 1 second for 1000 records
- **Redis Operations**: < 0.5 seconds for 100 operations
- **ChromaDB Search**: < 2 seconds for 50 searches
- **Document Processing**: < 3 seconds per document
- **Query Classification**: < 5 seconds for 20 queries

### Load Testing
- **Concurrent Database Queries**: 20 concurrent queries < 3 seconds
- **Concurrent Document Searches**: 15 concurrent searches < 5 seconds
- **Concurrent Query Processing**: 25 concurrent queries < 8 seconds

### Stress Testing
- **High Volume Document Processing**: 100 documents < 30 seconds
- **High Volume Query Processing**: 50 queries < 20 seconds
- **Memory Usage**: < 100MB increase under load

## Security Testing

### SQL Injection Prevention
- Tests for malicious SQL queries
- Prevention of DROP, INSERT, UPDATE, DELETE operations
- Input sanitization and validation

### Input Validation
- XSS prevention
- Path traversal prevention
- Command injection prevention
- File upload security

### Authentication & Authorization
- API key validation
- Rate limiting
- Session security
- CORS security

## Test Reports

### Coverage Reports
- HTML coverage report: `test-results/htmlcov/index.html`
- XML coverage report: `test-results/coverage.xml`

### Test Results
- JUnit XML reports: `test-results/*-tests.xml`
- Detailed JSON report: `test-results/detailed-report.json`
- Security scan: `test-results/security-scan.json`
- Safety report: `test-results/safety-report.json`

## CI/CD Integration

### GitHub Actions
The CI/CD pipeline runs all tests automatically:
- Unit tests with coverage
- Integration tests
- Performance tests
- Security tests
- End-to-end tests
- Frontend tests
- Security scanning

### Test Artifacts
Test results are uploaded as artifacts:
- Test reports
- Coverage reports
- Security scans
- Performance metrics

## Best Practices

### Writing Tests
1. **Isolation**: Each test should be independent
2. **Mocking**: Mock external dependencies
3. **Data**: Use realistic test data
4. **Assertions**: Clear and specific assertions
5. **Naming**: Descriptive test names

### Test Organization
1. **Grouping**: Group related tests in classes
2. **Fixtures**: Use fixtures for common setup
3. **Markers**: Use markers for test categorization
4. **Documentation**: Document complex test scenarios

### Performance Considerations
1. **Timeouts**: Set appropriate timeouts
2. **Resources**: Monitor resource usage
3. **Cleanup**: Clean up test data
4. **Parallelization**: Use parallel execution when possible

## Troubleshooting

### Common Issues
1. **Database Connection**: Ensure test database is available
2. **Redis Connection**: Ensure Redis is running
3. **ChromaDB Connection**: Ensure ChromaDB is accessible
4. **API Keys**: Set test API keys

### Debug Mode
Run tests in debug mode:
```bash
pytest tests/ -v -s --tb=long
```

### Verbose Output
Get detailed test output:
```bash
pytest tests/ -v --tb=short --durations=10
```

## Contributing

### Adding New Tests
1. Follow existing test patterns
2. Use appropriate fixtures
3. Add proper markers
4. Update documentation

### Test Maintenance
1. Keep tests up to date
2. Remove obsolete tests
3. Update fixtures as needed
4. Monitor test performance

## Support

For test-related issues:
1. Check test logs
2. Verify environment setup
3. Review test documentation
4. Contact development team
