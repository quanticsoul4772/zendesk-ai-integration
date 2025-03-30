# Code Coverage Guide

This document explains our code coverage goals, how we measure coverage, and how to maintain high coverage in the Zendesk AI Integration project.

## Coverage Goals

We maintain a risk-based approach to code coverage with specific targets for different components:

| Component Type | Target Coverage | Examples |
|----------------|-----------------|----------|
| **Core Components** | 85-90% | AI services, cache manager, batch processor, DB repository |
| **Support Components** | 70-80% | Zendesk client, report generators, CLI module |
| **Utility Components** | 60-70% | Helper functions, data classes |
| **Overall Project** | >75% | All components combined |

## Measuring Coverage

We use pytest-cov to measure code coverage. Here's how to run coverage analysis:

```bash
# Generate coverage for all tests with terminal and HTML report
pytest --cov=src --cov-report=term --cov-report=html

# Generate coverage for specific modules
pytest --cov=src/modules/cache_manager.py --cov-report=term

# Check if coverage meets minimum threshold
pytest --cov=src --cov-fail-under=75
```

After running the HTML report, open `htmlcov/index.html` in your browser to see detailed coverage information.

## Understanding Coverage Reports

The coverage report shows:

- **Line coverage**: Percentage of code lines executed during tests
- **Branch coverage**: Percentage of code branches (if/else, loops) executed
- **Missing lines**: Specific lines that weren't executed during tests

Look for:
- Functions with low coverage
- Conditional branches that aren't fully tested
- Error handling paths that aren't exercised

## Strategies for Maintaining High Coverage

### 1. Test-Driven Development (TDD)

Write tests before implementing features:
1. Write a failing test for the new functionality
2. Implement the code to make the test pass
3. Refactor while keeping tests passing
4. Check coverage and add tests for any missed paths

### 2. Target Complex Logic

Prioritize testing complex code paths:
- Error handling
- Conditional logic
- Exception paths
- Edge cases

### 3. Mock External Dependencies

Use fixtures in `tests/conftest.py` to mock:
- Zendesk API
- AI services (Claude, OpenAI)
- MongoDB database
- External APIs

### 4. Test Both Success and Failure Paths

For each function or method, test:
- Normal successful operation
- Edge cases
- Error conditions
- Resource failures (network, database)

### 5. Test Coverage in CI/CD

Our GitHub Actions workflow enforces coverage thresholds:
- PRs must maintain or improve coverage
- Coverage thresholds are checked for each component type
- Coverage reports are uploaded to Codecov for analysis

## Interpreting Codecov Reports

When a PR is submitted, Codecov will:
1. Show coverage changes in the PR
2. Flag any coverage decreases
3. Provide line-by-line annotations
4. Show component-level coverage metrics

Pay attention to:
- Coverage patches (lines changed by your PR)
- Sunburst diagram showing component coverage
- File-by-file breakdown

## Exempting Code from Coverage

In rare cases, some code may be exempted from coverage requirements:

```python
# Code that's difficult to test or deliberately not covered
def unreachable_in_tests():  # pragma: no cover
    """This function is only called in production environments."""
    pass
```

Use coverage exemptions sparingly and only with proper justification.

## Best Practices

1. **Check coverage locally** before submitting a PR
2. **Add tests for all new code** to maintain or improve coverage
3. **Focus on meaningful tests**, not just hitting lines
4. **Review coverage reports** to identify testing gaps
5. **Use coverage as a guide**, not an absolute metric

Remember that high coverage doesn't guarantee bug-free code, but it does increase confidence in the codebase and reduces the likelihood of regression issues.
