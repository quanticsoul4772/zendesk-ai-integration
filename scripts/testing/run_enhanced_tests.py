"""
Script to run enhanced test suite for Zendesk AI Integration.

This script bypasses the standard pytest discovery and runs the updated tests
that have been fixed to avoid skipping. 
"""

import os
import sys
import importlib
import pytest
import subprocess

# First, ensure psutil is installed
try:
    import psutil
    HAS_PSUTIL = True
    print("psutil detected, memory tests will be enabled")
except ImportError:
    print("Installing psutil...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        print("psutil installed successfully")
        import psutil
        HAS_PSUTIL = True
    except Exception as e:
        print(f"Failed to install psutil: {e}")
        HAS_PSUTIL = False

# Define the tests to run
enhanced_tests = [
    # Basic unit tests
    'tests/unit/test_cache_invalidation_fixed.py',
    'tests/unit/test_cache_invalidation_improved.py',
    
    # Fixed reporter tests
    'tests/unit/test_reporter_common.py',
    
    # Updated cache integration test
    'tests/integration/test_zendesk_cache_integration_updated.py',
    
    # Performance tests (will run with psutil now installed)
    'tests/performance/test_cache_performance.py::TestCachePerformance::test_cache_hit_rate_optimization',
    'tests/performance/test_cache_performance.py::TestCachePerformance::test_ttl_effectiveness',
    'tests/performance/test_cache_performance.py::TestCachePerformance::test_cache_memory_usage',
    'tests/performance/test_cache_performance.py::TestCachePerformance::test_concurrency_performance',
]

# Run the enhanced tests
print("\nRunning enhanced test suite:")
pytest.main(enhanced_tests + ["-v"])
