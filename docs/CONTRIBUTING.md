# Contributing to Zendesk AI Integration

Thank you for considering contributing to the Zendesk AI Integration project! This document provides guidelines and instructions for contributing to the project, with a special emphasis on testing and quality assurance.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

By participating in this project, you agree to abide by the following guidelines:

- Be respectful and inclusive in your communications
- Accept constructive criticism gracefully
- Focus on what is best for the community and project
- Show empathy towards other community members

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up your development environment (see below)
4. Create a feature branch for your work
5. Make your changes, with tests
6. Submit a pull request

## Development Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

5. Set up pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

6. Configure environment variables by creating a `.env` file (see README.md for required variables)

## Testing Requirements

**All contributions must include appropriate tests.** We maintain high test standards in this project:

### Test Coverage Requirements

- **New Features**: Must have at least 80% test coverage
- **Bug Fixes**: Must include a test that would have caught the bug
- **Refactoring**: Must maintain or improve existing test coverage

### Running Tests

Before submitting a pull request, please ensure all tests pass:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term

# Run specific test categories
pytest tests/unit
pytest tests/integration
pytest tests/functional
pytest tests/performance
```

### Writing Tests

1. **Unit Tests**: 
   - Place in `tests/unit/`
   - Focus on testing one component in isolation
   - Mock external dependencies
   - Name test files with `test_` prefix

2. **Integration Tests**:
   - Place in `tests/integration/`
   - Test interactions between multiple components
   - Use fixtures from `conftest.py` when possible

3. **Functional Tests**:
   - Place in `tests/functional/`
   - Test complete workflows or user stories
   - Focus on behavior rather than implementation details

4. **Performance Tests**:
   - Place in `tests/performance/`
   - For performance-critical components only
   - Include benchmarks with assertions

### Test Structure

Follow this structure for test methods:

```python
def test_specific_functionality_being_tested(self, fixtures):
    """Clear description of what this test verifies."""
    # Arrange - set up test data and conditions
    
    # Act - perform the action being tested
    
    # Assert - verify the expected outcome
```

For detailed guidance on testing, please refer to [TESTING.md](TESTING.md).

## Pull Request Process

1. Update the README.md or relevant documentation with details of your changes
2. Add or update tests as necessary
3. Ensure all tests pass and meet coverage requirements
4. Ensure code passes all pre-commit checks
5. Submit the pull request with a clear description of the changes

### PR Requirements Checklist

- [ ] Tests added for new functionality
- [ ] All existing tests pass
- [ ] Code coverage requirements met
- [ ] Documentation updated
- [ ] Pre-commit hooks pass
- [ ] PR describes changes clearly

## Coding Standards

This project uses flake8 for linting and enforces the following standards:

- Maximum line length: 100 characters
- Follow PEP 8 style guide
- Use consistent docstrings (flake8-docstrings)
- Organize imports with isort

These standards are enforced via pre-commit hooks and GitHub Actions.

## Documentation

Documentation is a crucial part of this project. Please update documentation when:

- Adding new features
- Changing existing functionality
- Deprecating features
- Fixing bugs with noteworthy implications

Documentation should be clear, concise, and include examples when relevant.

## Issue Reporting

When reporting issues, please include:

1. A clear and descriptive title
2. A detailed description of the issue
3. Steps to reproduce the problem
4. Expected behavior
5. Actual behavior
6. Screenshots if applicable
7. Environment information (OS, Python version, etc.)

---

Thank you for contributing to the Zendesk AI Integration project!
