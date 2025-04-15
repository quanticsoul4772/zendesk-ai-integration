# Pre-commit Setup Guide

This project uses pre-commit hooks to ensure code quality and consistency. These hooks run automatically before each commit to check for issues and prevent problematic code from being committed.

## Installation

To set up pre-commit hooks on your local development environment:

1. Install pre-commit:
   ```bash
   pip install pre-commit
   ```

2. Install the git hooks:
   ```bash
   pre-commit install
   ```

Once installed, the hooks will run automatically whenever you attempt to commit changes.

## Configured Hooks

Our project uses the following pre-commit hooks:

### Code Formatting & Style
- **trailing-whitespace**: Trims trailing whitespace at the end of lines
- **end-of-file-fixer**: Ensures files end with a newline
- **flake8**: Checks Python code for style and quality issues
- **isort**: Sorts Python imports consistently

### Validation
- **check-yaml**: Validates YAML files
- **check-added-large-files**: Prevents committing large files

### Testing
- **pytest-check**: Runs unit tests to ensure your changes don't break existing functionality

## Configuration

The pre-commit configuration is stored in `.pre-commit-config.yaml` in the project root. The current configuration includes:

```yaml
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
        additional_dependencies: [flake8-docstrings]
        exclude: ^(venv/|\.venv/|\.git/|tests/)
        args: [--max-line-length=100]

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort
        args: [--profile=black]

-   repo: local
    hooks:
    -   id: pytest-check
        name: pytest-check
        entry: pytest tests/unit
        language: system
        pass_filenames: false
        always_run: true
        stages: [commit]
```

## Usage

### Running Hooks Manually

You can run pre-commit hooks manually against all files:

```bash
pre-commit run --all-files
```

Or against specific files:

```bash
pre-commit run --files src/modules/cache_manager.py
```

### Skipping Hooks

In rare cases, when you need to bypass the pre-commit hooks (not recommended for normal development):

```bash
git commit -m "Your commit message" --no-verify
```

### Updating Hooks

To update the hooks to their latest versions:

```bash
pre-commit autoupdate
```

## Troubleshooting

If you encounter issues with pre-commit hooks:

1. **Hook installation problems**: Try reinstalling the hooks with `pre-commit install --force`
2. **Flake8 errors**: Review and fix the style issues, or adjust the configuration if necessary
3. **Failed tests**: Fix the failing tests before committing, or update the tests if your changes intentionally change behavior

## Benefits

Using pre-commit hooks provides several advantages:

- Catches issues early, before they're committed
- Ensures consistent code style throughout the project
- Prevents broken code from entering the repository
- Reduces the need for style-related code review comments
- Makes continuous integration (CI) runs more likely to succeed

These hooks complement our GitHub Actions CI workflow by catching issues locally before they reach the remote repository.
