"""
Configuration for parallel test execution using pytest-xdist.

This file contains configuration and fixtures needed for reliable parallel test execution.
Run tests in parallel by adding: pytest -n auto

Parallel test execution is especially useful for speeding up the test suite,
but requires proper test isolation to work correctly.
"""
import pytest
import os
import tempfile
import random

# Generate a unique node ID for this test worker
# This helps avoid conflicts when multiple test processes run simultaneously
@pytest.fixture(scope="session")
def worker_id(request):
    """Return the worker ID for parallel test execution."""
    if hasattr(request.config, 'workerinput'):
        # Running in parallel mode with pytest-xdist
        return request.config.workerinput['workerid']
    else:
        # Running in standard mode
        return "master"

# Use a unique temporary directory for each worker to avoid conflicts
@pytest.fixture(scope="session")
def worker_tmpdir(worker_id, tmp_path_factory):
    """Create a temporary directory for each worker."""
    base_temp = tmp_path_factory.getbasetemp() / worker_id
    base_temp.mkdir(exist_ok=True)
    return base_temp

# Function-scoped isolated temp directory for complete test isolation
@pytest.fixture
def isolated_temp_dir(worker_id, tmp_path):
    """Create an isolated temporary directory per test."""
    import random
    test_dir = tmp_path / f"test_{worker_id}_{random.randint(1000, 9999)}"
    test_dir.mkdir(exist_ok=True)
    return test_dir

# Use a unique MongoDB database name for each worker
@pytest.fixture(scope="session")
def mongodb_test_db_name(worker_id):
    """Generate a unique MongoDB database name for each worker."""
    return f"test_db_{worker_id}"

# Use different port ranges for mock servers per worker
@pytest.fixture(scope="session")
def worker_port_offset(worker_id):
    """Calculate port offset for this worker to avoid port conflicts."""
    if worker_id == "master":
        return 0
    else:
        # Extract the worker number and add an offset (8000, 9000, etc.)
        worker_num = int(worker_id.replace('gw', ''))
        return 1000 * (worker_num + 1)

# Ensure MongoDB fixture uses unique database per worker
@pytest.fixture(scope="session", autouse=True)
def patch_mongodb_fixture(mongodb_test_db_name, monkeypatch):
    """Patch MongoDB fixture to use worker-specific database."""
    monkeypatch.setenv("MONGODB_TEST_DB_NAME", mongodb_test_db_name)

# Ensure unique file names for file-based tests
@pytest.fixture
def unique_filename(worker_id):
    """Generate a unique filename for file-based tests with timestamp."""
    import time
    timestamp = int(time.time())
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
    return f"test_file_{worker_id}_{timestamp}_{random_suffix}.tmp"

# Time freezing fixture for deterministic testing with time-dependent code
@pytest.fixture
def frozen_time():
    """Freeze time for deterministic tests."""
    from unittest.mock import patch
    import time
    fixed_time = 1000000000  # Fixed timestamp
    
    # Patch various time functions
    with patch('time.time') as time_mock:
        time_mock.return_value = fixed_time
        
        # Create helper function to advance time
        def advance_time(seconds):
            nonlocal fixed_time
            fixed_time += seconds
            time_mock.return_value = fixed_time
            
        # Attach the helper to the mock
        time_mock.advance = advance_time
        yield time_mock

# Add custom markers for test categorization and selective running
def pytest_configure(config):
    """Configure custom test markers."""
    config.addinivalue_line("markers", 
                           "slow: marks tests as slow running (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", 
                           "serial: marks tests that cannot run in parallel")
    config.addinivalue_line("markers", 
                           "performance: marks performance tests")

# Handle tests that cannot run in parallel
def pytest_xdist_node_collection_finished(node, ids):
    """Handle serial tests when running in parallel mode with better detection."""
    if hasattr(node.config, 'workerinput'):
        # Get the worker ID
        worker_id = node.config.workerinput['workerid']
        worker_count = int(node.config.option.numprocesses)
        
        # More accurate detection of serial tests
        serial_test_ids = []
        
        # Common patterns for tests that should run serially
        serial_patterns = [
            "::test_serial_",
            "::TestSerial::",
            "::test_cache_invalidation",
            "::test_db_connection",
            "::test_file_lock",
            "::test_webhook_",
            "::test_rate_limit", 
            "::test_lock"
        ]
        
        for id in ids:
            # Check if this test matches any serial pattern
            if any(pattern in id for pattern in serial_patterns):
                serial_test_ids.append(id)
        
        # Skip serial tests on all workers except worker 0
        if worker_id != "gw0" and serial_test_ids:
            skip_ids = serial_test_ids
            print(f"Worker {worker_id}: Skipping {len(skip_ids)} serial tests")
            # Remove these tests from this worker
            for skip_id in skip_ids:
                if skip_id in ids:
                    ids.remove(skip_id)

# Optimize test fixture setup for parallel execution
@pytest.fixture(scope="session")
def expensive_shared_resource(worker_id):
    """Create an expensive resource once per worker with better isolation."""
    import time
    print(f"Worker {worker_id}: Setting up expensive shared resource")
    # Create a resource with worker-specific identifiers
    resource = {
        "id": worker_id,
        "data": f"shared_data_{worker_id}",
        "created_at": time.time()
    }
    yield resource
    print(f"Worker {worker_id}: Tearing down expensive shared resource")

# Improved cache testing fixtures
@pytest.fixture
def isolated_cache_manager(worker_id):
    """Create an isolated cache manager for clean cache testing."""
    import uuid
    from src.modules.cache_manager import CacheManager
    
    # Use a unique namespace for this test execution
    test_id = str(uuid.uuid4())[:8]
    cache_namespace = f"test_cache_{worker_id}_{test_id}"
    
    # Create an isolated instance
    cache = CacheManager(namespace=cache_namespace)
    
    # Clear any existing data
    cache.clear()
    
    yield cache
    
    # Clean up after test
    cache.clear()

# Optimize setup of common test data
@pytest.fixture(scope="session")
def common_test_data(worker_id):
    """Set up common test data once per worker session."""
    data = []
    # Generate test data - would normally be loaded from files or created
    for i in range(100):
        data.append({
            "id": f"{worker_id}_{i}",
            "value": f"test_value_{i}"
        })
    return data
