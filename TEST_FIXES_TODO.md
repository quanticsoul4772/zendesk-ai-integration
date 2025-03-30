# Test Fixes TODO

This document outlines the test fixes that need to be implemented to match the current implementation of the ZendeskClient class.

## Background

Several tests in `tests/unit/test_zendesk_client.py` were skipped because they did not match the current implementation of the ZendeskClient class. These tests need to be updated to properly test the actual functionality.

## Test Fixes Needed

### 1. `test_fetch_tickets_with_days_parameter`

**Issue:** The test assumes that the `fetch_tickets` method accepts a `days` parameter, but it doesn't in the current implementation.

**Fix needed:**
- Either update the implementation to support a `days` parameter
- Or modify the test to use a different approach to test date filtering

### 2. `test_fetch_views`

**Issue:** The current implementation of the cache integration is causing this test to fail.

**Fix needed:**
- Update the test to properly mock the cache layer
- Make sure the views are being correctly returned from the mocked client

### 3. `test_handle_rate_limiting`

**Issue:** The test does not match the actual rate limiting logic in the implementation.

**Fix needed:**
- Update the test to more accurately represent the rate limiting behavior
- Fix the assertion for the number of returned items

## Implementation Recommendations

1. **Add support for `days` parameter**: Consider adding a `days` parameter to the `fetch_tickets` method that can filter tickets based on creation or update date.

2. **Consistent cache behavior**: Make sure the cache behavior is consistent across all methods.

3. **Better rate limiting handling**: Ensure rate limiting retries are consistent and well-tested.

## Next Steps

1. After implementing these fixes, run the tests with `pytest -v tests/unit/test_zendesk_client.py` to verify they pass.
2. When updating any implementation, make sure to maintain backward compatibility where possible.
3. Update any relevant documentation to reflect the changes.
