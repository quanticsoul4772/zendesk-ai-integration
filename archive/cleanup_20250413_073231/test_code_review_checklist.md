# Test Code Review Checklist

Use this checklist when reviewing test code quality in the Zendesk AI Integration project.

## Test Organization

- [ ] Tests are organized in the correct directories (unit, integration, functional, performance)
- [ ] Each test file focuses on a single component or related functionality
- [ ] Test class and function names clearly communicate what's being tested
- [ ] Related tests are grouped in logical test classes

## Test Structure

- [ ] Tests follow the AAA pattern (Arrange-Act-Assert)
- [ ] Each test verifies a single behavior or scenario
- [ ] Fixture usage is appropriate and avoids test interdependence
- [ ] Complex setup is moved to fixtures or helper methods
- [ ] Test names clearly describe the scenario and expected outcome
- [ ] Tests avoid unnecessary abstraction that obscures their intent

## Test Effectiveness

- [ ] Tests cover both happy paths and error cases
- [ ] Edge cases are identified and tested
- [ ] Tests verify behavior, not implementation details where appropriate
- [ ] Assertions are specific and verify the right properties
- [ ] Tests don't contain logic bugs (conditionals, loops)
- [ ] Mocks are used appropriately and don't over-specify

## Test Maintainability

- [ ] Tests don't duplicate setup code unnecessarily
- [ ] Tests avoid magic numbers and strings (use constants or variables)
- [ ] Tests aren't brittle (tightly coupled to implementation details)
- [ ] Test data is clearly separated from test logic
- [ ] Tests don't contain commented-out code
- [ ] Parameterized tests are used for testing similar scenarios with different inputs

## Performance Considerations

- [ ] Tests don't take unnecessarily long to run
- [ ] Heavy setup is done at the class or module level when possible
- [ ] Database tests use in-memory databases when possible
- [ ] Tests clean up resources properly (files, connections, etc.)
- [ ] Performance-sensitive tests are properly marked

## Documentation

- [ ] Test function docstrings clearly explain what is being tested
- [ ] Complex test scenarios have additional comments explaining the setup
- [ ] Test data generation is documented if not obvious
- [ ] Rationale for unusual testing approaches is documented

## Reviewing Results

After reviewing each test file, categorize issues as:

1. **Critical**: Tests that are unreliable, don't verify what they claim to, or are missing essential scenarios
2. **Major**: Tests with structural problems, excessive duplication, or poor design
3. **Minor**: Style issues, minor refactoring opportunities, or documentation improvements

Document issues found and prioritize addressing them based on risk and importance.
