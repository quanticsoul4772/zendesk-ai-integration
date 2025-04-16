# Legacy Mode Removal Guide

This guide provides detailed steps for removing legacy components from the codebase while ensuring all functionality continues to work correctly.

## Overview

The process of removing legacy components is divided into the following steps:

1. **Backup legacy files** - Create backups of all legacy components
2. **Update imports** - Update import statements to use compatibility adapters
3. **Test compatibility** - Run tests to ensure compatibility adapters work correctly
4. **Remove legacy files** - Once all references are updated, remove the legacy files
5. **Verify functionality** - Run the full test suite to ensure nothing broke

## Step-by-Step Instructions

### 1. Backup Legacy Files

First, create backups of all legacy components to ensure we can restore them if needed:

```bash
python scripts/backup_legacy_files.py
```

This will create timestamped copies of all legacy files in `src/modules/backups`.

### 2. Update References

Next, analyze the codebase to find all references to legacy components:

```bash
python scripts/analyze_legacy_references.py
```

This will generate reports showing all references to legacy components in the codebase.

Then, update all imports to use the compatibility adapters:

```bash
# First, do a dry run to see what would change
python scripts/update_imports.py --dry-run

# If the changes look good, run it for real
python scripts/update_imports.py
```

### 3. Test Compatibility

Run the compatibility adapter tests to ensure they correctly implement the legacy interfaces:

```bash
python -m unittest tests/unit/test_compatibility_adapters.py
```

Then run the full test suite to ensure everything still works:

```bash
python run_tests.py
```

### 4. Remove Legacy Files

Once all references are using the compatibility adapters and tests pass, remove the legacy files:

1. `src/modules/ai_analyzer.py`
2. `src/modules/cache_manager.py`
3. `src/modules/db_repository.py`
4. `src/modules/report_generator.py`
5. `src/modules/reporters/` (directory)
6. `src/modules/scheduler.py`
7. `src/modules/webhook_server.py`
8. `src/modules/zendesk_client.py`
9. `src/infrastructure/utils/service_provider.py`

You can use the following script to remove the files:

```python
import os
import shutil

# Base directory
root_dir = "src"

# Files to remove
files_to_remove = [
    os.path.join(root_dir, "modules", "ai_analyzer.py"),
    os.path.join(root_dir, "modules", "cache_manager.py"),
    os.path.join(root_dir, "modules", "db_repository.py"),
    os.path.join(root_dir, "modules", "report_generator.py"),
    os.path.join(root_dir, "modules", "scheduler.py"),
    os.path.join(root_dir, "modules", "webhook_server.py"),
    os.path.join(root_dir, "modules", "zendesk_client.py"),
    os.path.join(root_dir, "infrastructure", "utils", "service_provider.py"),
]

# Directories to remove
dirs_to_remove = [
    os.path.join(root_dir, "modules", "reporters"),
]

# Remove files
for file_path in files_to_remove:
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Removed file: {file_path}")

# Remove directories
for dir_path in dirs_to_remove:
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
        print(f"Removed directory: {dir_path}")
```

### 5. Verify Functionality

Run the full test suite again to ensure everything still works after removing the legacy files:

```bash
python run_tests.py
```

Also, run any manual tests or integration tests to ensure the application works correctly:

```bash
python zendesk_cli.py --help
```

## Rollback Strategy

If issues are encountered during the process, follow these steps to roll back:

1. Restore from backups:
   ```bash
   # Copy files from backups to their original locations
   cp -r src/modules/backups/ai_analyzer_* src/modules/ai_analyzer.py
   cp -r src/modules/backups/cache_manager_* src/modules/cache_manager.py
   # ... and so on for each component
   ```

2. If using Git, you can also reset to the previous state:
   ```bash
   git reset --hard HEAD^
   ```

## Monitoring

After removing legacy components, monitor the application for any issues:

1. Check logs for errors or warnings
2. Monitor performance metrics
3. Get feedback from users

## Next Steps

After successfully removing legacy components, consider these next steps:

1. **Refactor Compatibility Layer** - Gradually move code from using compatibility adapters to using the new components directly
2. **Update Documentation** - Update documentation to reflect the new architecture
3. **Remove Compatibility Layer** - Once all code is using the new components directly, remove the compatibility layer
4. **Code Cleanup** - Do a final pass to remove any remaining legacy code or comments

## Success Criteria

The legacy mode removal is considered successful when:

1. All legacy components have been removed
2. All tests pass successfully
3. The application works correctly in all scenarios
4. No references to legacy components remain in the codebase
5. The code is cleaner and easier to maintain
