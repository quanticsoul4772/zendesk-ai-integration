- [Complex Test Examples](docs/complex_test_examples_index.md): Advanced test scenarios for challenging use cases# Comprehensive Testing Guide for Zendesk AI Integration

This document outlines the complete testing strategy, structure, and best practices for the Zendesk AI Integration project. It serves as the primary reference for anyone working on or contributing to the testing of this application.

## 1. Test Structure and Organization

The testing suite is organized hierarchically according to the testing pyramid principle, which emphasizes having more unit tests than integration or functional tests:

```
tests/
├── unit/                  # Unit tests for individual components
│   ├── test_ai_services.py
│   ├── test_cache_manager.py
│   └── ...
├── integration/           # Integration tests for component interactions
│   ├── test_ai_db_integration.py
│   └── ...
├── functional/            # Functional/workflow tests
│   ├── test_workflows.py
│   └── ...
├── performance/           # Performance tests
│   ├── test_batch_performance.py
│   └── ...
├── conftest.py            # Shared fixtures
├── test_utils.py          # Testing utilities
└── data/                  # Test data files
```

### Testing Pyramid Implementation

Following industry best practices, our test distribution follows this pattern:

1. **Unit Tests (70% of tests)**: Fast tests focusing on individual functions or classes in isolation, with all dependencies mocked.
2. **Integration Tests (20% of tests)**: Testing how components interact with each other, typically involving 2-3 real components with other dependencies mocked.
3. **Functional/E2E Tests (10% of tests)**: Verifying complete workflows from end to end, simulating real user interactions with minimal mocking.

## 2. Test Coverage Goals

We follow a risk-based approach to test coverage, prioritizing critical components:

1. **Core Components (High Risk/Impact)**: 
   - Target: 85-90% code coverage
   - Includes: AI services, cache manager, batch processor, database repository
   - Reasoning: These components affect core application functionality and data integrity

2. **Support Components (Medium Risk/Impact)**:
   - Target: 70-80% code coverage
   - Includes: Zendesk client, report generators, CLI module
   - Reasoning: These components are important but have less impact on core functionality

3. **Utility Components (Lower Risk/Impact)**:
   - Target: 60-70% code coverage
   - Includes: Helper functions, simple data classes
   - Reasoning: These components are often simple and less likely to contain complex bugs

Overall project target: >75% code coverage

> **Note**: Code coverage should be viewed as a guide, not an absolute target. A high coverage percentage with poor quality tests is worse than a slightly lower percentage with thoughtful, comprehensive tests.

## 3. Mocking External Dependencies

One of the most important aspects of testing applications with external API dependencies is properly mocking these dependencies to ensure tests are fast, reliable, and independent of external services.

### Mock Fixtures Available

The project's `conftest.py` provides these key fixtures:

```python
# Mock environment variables
@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Set up mock environment variables for testing."""
    with patch.dict(os.environ, {
        "ZENDESK_EMAIL": "test@example.com",
        "ZENDESK_API_TOKEN": "test_token",
        "ZENDESK_SUBDOMAIN": "testsubdomain",
        "OPENAI_API_KEY": "test_openai_key",
        "ANTHROPIC_API_KEY": "test_anthropic_key",
        "MONGODB_URI": "mongodb://localhost:27017",
        "MONGODB_DB_NAME": "test_db",
        "MONGODB_COLLECTION_NAME": "test_collection"
    }):
        yield

# Mock Zendesk client
@pytest.fixture
def mock_zendesk_client():
    """Create a mock Zendesk client for testing."""
    with patch('src.modules.zendesk_client.Zenpy') as mock_zenpy:
        client_instance = MagicMock()
        mock_zenpy.return_value = client_instance
        yield client_instance

# Mock Claude service
@pytest.fixture
def mock_claude_service():
    """Create a mock for Claude service API calls."""
    with patch('src.claude_service.call_claude_with_retries') as mock_call:
        # Configure default successful response
        mock_call.return_value = {
            "sentiment": {
                "polarity": "negative",
                "urgency_level": 3,
                "frustration_level": 4,
                "business_impact": {"detected": True}
            },
            "category": "hardware_issue",
            "component": "gpu",
            "confidence": 0.85
        }
        yield mock_call
```

### Using Mock Fixtures

When writing tests, import the necessary fixtures and use them to mock external dependencies:

```python
def test_something(mock_zendesk_client, mock_claude_service):
    # The external dependencies will be automatically mocked
    # Configure mock return values specific to this test if needed
    mock_zendesk_client.tickets.get.return_value = create_test_ticket()
    
    # Test your function that uses Zendesk client
    result = process_ticket(ticket_id=1)
    
    # Assertions...
    assert result is not None
```

### Creating New Mocks

When adding new external dependencies, follow these guidelines:

1. Create a fixture in `conftest.py` for reusability
2. Use `unittest.mock.patch` to intercept external calls
3. Return appropriate test data (minimal but sufficient for testing)
4. Document the fixture with a clear docstring explaining its purpose and usage

## 4. Running Tests

### Basic Test Run

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/functional
pytest tests/performance

# Run with coverage report
pytest --cov=src --cov-report=html

# Run only MongoDB-related performance tests
pytest tests/performance/test_db_performance.py -m mongodb
```

### Test Configuration

Tests use fixtures defined in `tests/conftest.py` for common setup. Environment variables for testing are mocked automatically.

### Running Tests in Parallel

For faster test execution, especially during development:

```bash
# Install pytest-xdist if not already installed
pip install pytest-xdist

# Run tests in parallel using all available CPU cores
pytest -n auto

# Specify number of parallel processes
pytest -n 4
```

See the [Parallel Testing](#parallel-testing) section in our [Test Optimization Guide](docs/test_optimization_guidelines.md) for more details.

## 5. Performance Testing

The project includes comprehensive performance tests to ensure the system functions efficiently under various conditions:

### Batch Processing Tests

Located in `tests/performance/test_batch_processing.py`:
- Tests different batch sizes and worker thread configurations
- Measures throughput (items/second) for different configurations
- Evaluates error handling performance under different error scenarios

### Cache Performance Tests

Located in `tests/performance/test_cache_performance.py`:
- Tests cache hit rate optimization
- Evaluates TTL effectiveness
- Measures memory usage at different cache sizes

### Database Tests

Located in `tests/performance/test_db_performance.py`:
- Tests query performance for different query patterns
- Evaluates bulk operation efficiency
- Tests connection pool optimization

### Running Performance Tests

```bash
# Run all performance tests
pytest tests/performance

# Run specific performance test category
pytest tests/performance/test_cache_performance.py
```

> **Note**: Database performance tests require a MongoDB instance and are marked with the `mongodb` marker. If you don't have MongoDB installed, skip these tests with `pytest -k "not mongodb"`.

## 6. CI/CD Integration

Tests run automatically in GitHub Actions:
- On push to main branch
- On pull requests to main branch
- Matrix testing across Python 3.9, 3.10, and 3.11

The workflow is defined in `.github/workflows/python-tests.yml` and includes:

1. **Testing**: Running unit, integration, and functional tests with coverage
2. **Linting**: Checking code style with flake8 and isort
3. **Performance**: Running performance benchmarks
4. **Documentation**: Building and publishing documentation on successful merge to main

Coverage reports are automatically uploaded to Codecov.

### Coverage Thresholds

The CI pipeline enforces these minimum coverage thresholds:
- 85% for core components
- 75% for support components
- 70% overall code coverage

### Viewing CI Results

- GitHub repository → Actions tab → Latest workflow run
- Badge in README indicates current build status
- Codecov reports show coverage details and trends

## 7. Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality before commits. This catches issues early in the development process.

### Installation

```bash
pip install pre-commit
pre-commit install
```

### Available Hooks

Pre-commit runs these hooks automatically before each commit:
- Linting with flake8
- Import sorting with isort
- Basic unit tests
- File formatting checks

See [PRE_COMMIT_SETUP.md](PRE_COMMIT_SETUP.md) for detailed setup instructions.

## 8. Adding New Tests

When adding new functionality, follow this process:

1. Start with unit tests for the new component
2. Add integration tests if the component interacts with others
3. Update functional tests if the component affects workflows
4. Consider adding performance tests for performance-critical components

### Guidelines for Writing Good Tests

1. **Use Descriptive Test Names**: 
   - Names should clearly describe the scenario being tested
   - Format: `test_<function>_<scenario>_<expected_outcome>`
   - Example: `test_analyze_ticket_rate_limit_handles_exception`

2. **Follow AAA Pattern**: 
   - **Arrange**: Set up the test data and environment
   - **Act**: Call the function or method being tested
   - **Assert**: Verify the expected outcome
   - Separate these phases with blank lines for readability

3. **Use Assertions Correctly**: 
   - Be specific about what you're testing
   - Test one logical concept per test function
   - Use helpful assertion messages for clearer test failures

4. **Isolate Tests**: 
   - Each test should be independent of others
   - Don't rely on state from previous tests
   - Reset any shared resources between tests

5. **Test Edge Cases**: 
   - Test the happy path (normal operation)
   - Test boundary values and edge cases
   - Test error handling and exception paths

## 9. Test Examples

This section provides basic examples of different test types. For more complex testing scenarios and advanced techniques, see the [Complex Test Examples](docs/complex_test_examples_index.md) documentation.

### Unit Testing Example

This example demonstrates unit testing for the Claude service:

```python
# tests/unit/test_claude_service.py
import pytest
from unittest.mock import patch, MagicMock
from src.claude_service import analyze_ticket_content, ClaudeServiceError, RateLimitError

class TestClaudeService:
    """Test suite for Claude service functionality."""
    
    def test_analyze_ticket_content_success(self, mock_claude_service):
        """Test successful ticket content analysis."""
        # Arrange
        content = "I'm having problems with my GPU. System keeps crashing during rendering."
        
        mock_claude_service.return_value = {
            "sentiment": "negative",
            "category": "hardware_issue",
            "component": "gpu",
            "confidence": 0.9
        }
        
        # Act
        result = analyze_ticket_content(content)
        
        # Assert
        assert result["sentiment"] == "negative"
        assert result["category"] == "hardware_issue"
        assert result["component"] == "gpu"
        assert result["confidence"] == 0.9
        assert "error" not in result
        
    def test_analyze_ticket_content_rate_limit(self, mock_claude_service):
        """Test handling of rate limit errors."""
        # Arrange
        content = "Test content"
        mock_claude_service.side_effect = RateLimitError("Rate limit exceeded")
        
        # Act
        result = analyze_ticket_content(content)
        
        # Assert
        assert result["sentiment"] == "unknown"
        assert result["category"] == "uncategorized"
        assert result["component"] == "none"
        assert result["confidence"] == 0.0
        assert "error" in result
        assert "Rate limit exceeded" in result["error"]
```

### Integration Testing Example

This example shows integration testing between the Zendesk client and cache manager:

```python
# tests/integration/test_zendesk_cache_integration.py
import pytest
from unittest.mock import patch, MagicMock

from src.modules.zendesk_client import ZendeskClient
from src.modules.cache_manager import ZendeskCache

class TestZendeskCacheIntegration:
    """Integration tests for Zendesk Client and Cache Manager."""
    
    @pytest.fixture
    def mock_zenpy(self):
        """Fixture for mocked Zenpy client."""
        with patch('src.modules.zendesk_client.Zenpy') as mock_zenpy_class:
            mock_client = MagicMock()
            
            # Configure search to return mock tickets
            mock_tickets = [MagicMock() for _ in range(2)]
            for i, ticket in enumerate(mock_tickets):
                ticket.id = str(i+1)
                ticket.subject = f"Test {i+1}"
                ticket.description = f"Description {i+1}"
                ticket.status = "open"
            
            mock_client.search.return_value = mock_tickets
            mock_zenpy_class.return_value = mock_client
            yield mock_client
    
    def test_cached_ticket_fetch(self, mock_zenpy):
        """Test that tickets are cached and subsequent fetches use cache."""
        # Arrange
        client = ZendeskClient()
        
        # Act
        tickets_first = client.fetch_tickets(status="open", limit=10)
        tickets_second = client.fetch_tickets(status="open", limit=10)
        
        # Assert
        assert mock_zenpy.search.call_count == 1  # API called only once
        assert len(tickets_first) == len(tickets_second)
        assert tickets_first[0].id == tickets_second[0].id  # Same data returned
```

### Functional Testing Example

Here's an example of a functional test for a complete workflow:

```python
# tests/functional/test_workflows.py
import pytest
from unittest.mock import patch, MagicMock

from src.zendesk_ai_app import process_pending_tickets

class TestWorkflows:
    """Functional tests for end-to-end workflows."""
    
    @pytest.fixture
    def mock_components(self):
        """Set up mocks for all components."""
        with patch('src.modules.zendesk_client.ZendeskClient') as mock_zendesk, \
             patch('src.claude_service.analyze_ticket_content') as mock_analyze, \
             patch('src.modules.db_repository.DbRepository') as mock_db:
            
            # Configure mock tickets
            mock_ticket = MagicMock()
            mock_ticket.id = "123"
            mock_ticket.subject = "Test Ticket"
            mock_ticket.description = "Having issues with my GPU"
            mock_zendesk.return_value.fetch_tickets.return_value = [mock_ticket]
            
            # Configure mock analysis
            mock_analyze.return_value = {
                "sentiment": "negative",
                "category": "hardware_issue",
                "component": "gpu",
                "confidence": 0.9
            }
            
            yield {
                "zendesk": mock_zendesk.return_value,
                "analyze": mock_analyze,
                "db": mock_db.return_value
            }
    
    def test_process_pending_tickets_workflow(self, mock_components):
        """Test the complete workflow of processing pending tickets."""
        # Act
        results = process_pending_tickets(days=7, view_id=None)
        
        # Assert
        # Verify Zendesk client was called correctly
        mock_components["zendesk"].fetch_tickets.assert_called_once()
        
        # Verify analysis was performed
        mock_components["analyze"].assert_called_once()
        
        # Verify results were saved to database
        mock_components["db"].save_analysis.assert_called_once()
        
        # Verify workflow produced expected output
        assert len(results) == 1
        assert results[0]["ticket_id"] == "123"
        assert results[0]["component"] == "gpu"
```

## 10. Test Optimization

Refer to these resources for optimizing test performance:

- [Test Optimization Guide](test_optimization_guide.md): Comprehensive guide to test performance optimization
- [Test Optimization Guidelines](docs/test_optimization_guidelines.md): Specific strategies with code examples
- [Test Execution Trends](#tracking-performance-trends): Tools for tracking test performance over time

## 11. Test Checklist

When implementing new features or fixing bugs:

- [ ] Unit tests cover both normal operation and edge cases
- [ ] Integration tests verify component interactions
- [ ] Functional tests validate complete workflows
- [ ] Performance tests for performance-critical components 
- [ ] Pre-commit hooks pass
- [ ] CI pipeline passes
- [ ] Code coverage meets targets

## 12. Implementation Plan Status

The testing implementation follows this phased approach:

1. ✅ **Phase 1 - Core Test Infrastructure**:
   - Set up test directory structure
   - Create conftest.py with common fixtures
   - Implement first unit tests for AI services

2. ✅ **Phase 2 - Critical Component Tests**:
   - Complete unit tests for core components
   - Implement initial integration tests

3. ✅ **Phase 3 - Workflow and Performance Tests**:
   - Add functional workflow tests
   - Implement performance benchmarks

4. ✅ **Phase 4 - CI/CD and Documentation**:
   - Set up GitHub Actions workflow
   - Create testing documentation

5. ✅ **Phase 8 - Documentation and CI/CD**:
   - Enhance documentation
   - Set up code coverage reporting
   - Create contributing guidelines

6. ✅ **Phase 9 - Maintenance and Review**:
   - Review and optimize test code
   - Identify and fix test coverage gaps
   - Update documentation with best practices

## 13. Troubleshooting Common Test Issues

### Issue: Tests fail in CI but pass locally

- Check environment differences (Python version, dependencies)
- Verify tests aren't relying on local file paths or configurations
- Look for timing-sensitive tests that might be flaky

### Issue: Slow test execution

- Run the test optimizer: `python tools/optimize_tests.py`
- Check for tests making real external calls instead of using mocks
- Look for redundant setup that could be moved to fixtures

### Issue: Low test coverage

- Run the coverage gap analyzer: `python tools/identify_test_gaps.py`
- Focus on adding tests for high-risk components first
- Look for untested edge cases and error handling paths

## 14. Further Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Test-Driven Development Guide](https://www.agilealliance.org/glossary/tdd/)
- [Mocking Best Practices](https://docs.python.org/3/library/unittest.mock.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Complex Test Examples](docs/complex_test_examples_index.md): Advanced test scenarios for challenging use cases
