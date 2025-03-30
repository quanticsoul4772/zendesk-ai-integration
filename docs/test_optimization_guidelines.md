# Test Optimization Guidelines

This document provides detailed strategies for optimizing slow-running tests in the Zendesk AI Integration project, including examples of common issues and their solutions.

## Common Performance Issues and Solutions

### 1. Slow External API Mocks

**Problem**: Tests calling external services (Zendesk, OpenAI, Claude) are slow even with mocks.

**Solutions**:

#### Improve Mock Implementation

```python
# SLOW: Complex mock implementation
@pytest.fixture
def mock_zendesk_client(monkeypatch):
    mock_client = MagicMock()
    mock_tickets = []
    for i in range(100):  # Creating many mock objects
        ticket = MagicMock()
        ticket.id = i
        ticket.subject = f"Test ticket {i}"
        ticket.description = "..." * 1000  # Large string
        mock_tickets.append(ticket)
    
    mock_client.search.return_value = mock_tickets
    monkeypatch.setattr('src.modules.zendesk_client.Zenpy', lambda *args, **kwargs: mock_client)
    return mock_client

# OPTIMIZED: Only create what you need
@pytest.fixture
def mock_zendesk_client(monkeypatch):
    mock_client = MagicMock()
    # Create a generator instead of full list
    def ticket_generator():
        for i in range(100):
            ticket = MagicMock()
            ticket.id = i
            ticket.subject = f"Test ticket {i}"
            # Only add minimal required attributes
            yield ticket
    
    mock_client.search.return_value = ticket_generator()
    monkeypatch.setattr('src.modules.zendesk_client.Zenpy', lambda *args, **kwargs: mock_client)
    return mock_client
```

#### Use Fixture Scoping

```python
# SLOW: Function-scoped fixture recreated for each test
@pytest.fixture
def mock_zendesk_client(monkeypatch):
    # ... setup code ...
    return mock_client

# OPTIMIZED: Module or session-scoped fixture created once
@pytest.fixture(scope="module")
def mock_zendesk_client(monkeypatch):
    # ... setup code ...
    return mock_client
```

### 2. Database-Related Slowness

**Problem**: Tests involving MongoDB operations are slow.

**Solutions**:

#### Use In-Memory MongoDB for Tests

```python
# In conftest.py
@pytest.fixture(scope="session")
def in_memory_mongodb():
    """Create an in-memory MongoDB instance for testing."""
    import mongomock
    return mongomock.MongoClient()

@pytest.fixture
def mock_db_repository(in_memory_mongodb, monkeypatch):
    """Use in-memory MongoDB for repository tests."""
    db = in_memory_mongodb["test_db"]
    collection = db["test_collection"]
    
    # Patch the MongoDB client creation
    monkeypatch.setattr(
        'src.modules.db_repository.MongoClient',
        lambda *args, **kwargs: in_memory_mongodb
    )
    
    return collection
```

#### Optimize Database Interactions

```python
# SLOW: Many individual operations
def test_batch_insert(mock_db_repository):
    repo = DbRepository()
    for i in range(100):
        repo.insert_one({"id": i, "data": f"test_{i}"})  # 100 separate calls
    
    results = repo.find_all()
    assert len(results) == 100

# OPTIMIZED: Batch operations
def test_batch_insert(mock_db_repository):
    repo = DbRepository()
    items = [{"id": i, "data": f"test_{i}"} for i in range(100)]
    repo.insert_many(items)  # Single batch operation
    
    results = repo.find_all()
    assert len(results) == 100
```

### 3. Duplicate Setup in Multiple Tests

**Problem**: Similar tests duplicate expensive setup operations.

**Solutions**:

#### Use Parameterized Tests

```python
# SLOW: Multiple similar test methods
def test_sentiment_analysis_positive(mock_ai_service):
    result = analyze_sentiment("I love this product")
    assert result["sentiment"] == "positive"

def test_sentiment_analysis_negative(mock_ai_service):
    result = analyze_sentiment("I hate this product")
    assert result["sentiment"] == "negative"

def test_sentiment_analysis_neutral(mock_ai_service):
    result = analyze_sentiment("This product exists")
    assert result["sentiment"] == "neutral"

# OPTIMIZED: Parameterized test
@pytest.mark.parametrize("text,expected", [
    ("I love this product", "positive"),
    ("I hate this product", "negative"),
    ("This product exists", "neutral"),
])
def test_sentiment_analysis(mock_ai_service, text, expected):
    result = analyze_sentiment(text)
    assert result["sentiment"] == expected
```

#### Use Class-Level Setup

```python
# SLOW: Repeating setup in functions
def test_cache_hit(mock_zendesk_client):
    # Setup cache with data
    cache = ZendeskCache()
    cache.set("key1", "value1")
    # Test cache hit
    assert cache.get("key1") == "value1"

def test_cache_miss(mock_zendesk_client):
    # Setup cache with data again
    cache = ZendeskCache()
    cache.set("key1", "value1")
    # Test cache miss
    assert cache.get("key2") is None

# OPTIMIZED: Class with setup
class TestZendeskCache:
    @pytest.fixture(autouse=True)
    def setup(self, mock_zendesk_client):
        self.cache = ZendeskCache()
        self.cache.set("key1", "value1")
    
    def test_cache_hit(self):
        assert self.cache.get("key1") == "value1"
    
    def test_cache_miss(self):
        assert self.cache.get("key2") is None
```

### 4. Slow Performance Tests

**Problem**: Performance tests take too long to run and slow down the test suite.

**Solutions**:

#### Separate Fast and Slow Tests

```python
# Mark slow performance tests
@pytest.mark.slow
def test_batch_processor_large_dataset():
    # ... slow performance test ...

# In pytest.ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')

# Run only fast tests
# pytest -m "not slow"

# Run only slow tests
# pytest -m "slow"
```

#### Reduce Test Data Size for Regular Tests

```python
# SLOW: Large test data
def test_batch_processor():
    processor = BatchProcessor()
    data = [i for i in range(10000)]  # Large dataset
    result = processor.process(data)
    assert len(result) == 10000

# OPTIMIZED: Smaller test data with size parameter
@pytest.mark.parametrize("data_size", [10, 100, 1000])
def test_batch_processor(data_size):
    processor = BatchProcessor()
    data = [i for i in range(data_size)]
    result = processor.process(data)
    assert len(result) == data_size

# Only use large data in performance tests
@pytest.mark.slow
def test_batch_processor_performance():
    processor = BatchProcessor()
    data = [i for i in range(10000)]
    result = processor.process(data)
    assert len(result) == 10000
```

### 5. File I/O Slowdowns

**Problem**: Tests that read/write files are slow.

**Solutions**:

#### Use StringIO Instead of File I/O

```python
# SLOW: Actual file operations
def test_report_generator():
    generator = ReportGenerator()
    output_file = "test_report.txt"
    generator.generate_report(output_file)
    
    with open(output_file, "r") as f:
        content = f.read()
    
    assert "Summary" in content
    os.remove(output_file)  # Cleanup

# OPTIMIZED: Use StringIO
def test_report_generator():
    import io
    generator = ReportGenerator()
    output = io.StringIO()
    generator.generate_report(file_obj=output)
    
    content = output.getvalue()
    assert "Summary" in content
```

#### Mock File Operations

```python
# Using pytest's tmp_path fixture
def test_file_operations(tmp_path):
    test_file = tmp_path / "test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    
    # Test file reading functionality
    result = read_and_process_file(test_file)
    assert result == "PROCESSED: Test content"
```

## Advanced Optimization Techniques

### 1. Parallel Testing with pytest-xdist

Add pytest-xdist to your requirements-dev.txt:
```
pytest-xdist==2.5.0
```

Run tests in parallel:
```bash
pytest -n auto  # Uses all available CPU cores
```

This works best when:
- Tests are properly isolated (no shared state)
- Tests don't depend on specific ordering
- Your test suite has many independent tests

### 2. Test Case Prioritization

Organize tests by execution time to run fast tests first:

```python
# Fast test (runs first)
@pytest.mark.priority(1)
def test_simple_validation():
    # Quick test

# Medium test (runs second)
@pytest.mark.priority(2)
def test_moderate_complexity():
    # Moderate test

# Slow test (runs last)
@pytest.mark.priority(3)
def test_complex_scenario():
    # Complex/slow test
```

### 3. Optimizing Test Fixtures

#### Use yield fixtures for better resource management

```python
@pytest.fixture
def optimized_db_fixture():
    # Setup code
    db = setup_test_database()
    yield db
    # Teardown code - automatically runs after test completes
    db.cleanup()
```

#### Cache expensive computations

```python
# Cache fixture results (computed once per session)
@pytest.fixture(scope="session")
def expensive_computation(request):
    return cached_or_compute_result()
```

## Measuring Test Performance

### Using pytest-benchmark

Add to your requirements-dev.txt:
```
pytest-benchmark==3.4.1
```

Use in tests:
```python
def test_performance_critical_function(benchmark):
    # This will run the function multiple times and provide stats
    result = benchmark(performance_critical_function)
    assert result == expected_result
```

### Profiling Slow Tests

Add a profiling decorator:
```python
import cProfile
import pstats
from functools import wraps

def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        profile_filename = f"{func.__name__}.prof"
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        
        # Print top 10 time-consuming functions
        stats = pstats.Stats(profile_filename)
        stats.strip_dirs().sort_stats('cumtime').print_stats(10)
        
        return result
    return wrapper

# Use in test
@profile
def test_slow_function():
    result = slow_function()
    assert result is not None
```

## Implementation Checklist

When optimizing tests, work through this checklist:

1. [ ] Run test optimization tool to identify slow tests
2. [ ] Review fixture scopes - adjust to module/session where possible
3. [ ] Check for missing or inefficient mocks
4. [ ] Identify and parameterize similar tests
5. [ ] Separate slow performance tests with markers
6. [ ] Add parallel testing support with pytest-xdist
7. [ ] Profile the slowest tests to find bottlenecks
8. [ ] Reduce test data sizes where appropriate
9. [ ] Optimize file and database operations
10. [ ] Re-run optimization tool to measure improvements

By methodically applying these optimization techniques, you can significantly reduce test execution time while maintaining comprehensive test coverage.
