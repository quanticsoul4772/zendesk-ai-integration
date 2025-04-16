# Clean Architecture Cleanup Plan

This document lists the files and directories that can be safely removed from the Zendesk AI Integration project now that we've successfully transitioned to the clean architecture implementation.

## Overview

The project has been refactored to follow clean architecture principles, with proper separation of concerns between domain, application, infrastructure, and presentation layers. This allows us to remove legacy code that has been replaced by the new implementation.

## Files and Directories to Remove

### Legacy Modules

The `src/modules` directory contains legacy code that has been replaced by the clean architecture implementation:

```
src/modules/
```

This directory can be entirely removed as all functionality has been migrated to the clean architecture layers.

### Legacy Files in Root Directory

These files in the root directory are related to the legacy implementation and can be removed:

```
zendesk_menu.py
zendesk_menu.sh
zendesk_menu.bat
zendesk_ai_app.py
zendesk_ai_app.bat
```

### Legacy Files in src Directory

The following files in the `src` directory are legacy implementations that have been replaced:

```
src/ai_service.py
src/analyze_and_update_ticket.py
src/claude_enhanced_sentiment.py
src/claude_service.py
src/enhanced_sentiment.py
src/mongodb_helper.py
src/unified_ai_service.py
src/unified_sentiment.py
src/zendesk_ai_app.py
```

### Refactored Directory

The `src/refactored` directory was a transitional directory used during the refactoring process and can be removed:

```
src/refactored/
```

### Temporary Files

Legacy references and dependency graphs generated during the transition process:

```
dependency_graph_20250412_*.txt
legacy_references_20250412_*.csv
legacy_summary_20250412_*.txt
import_update_report_20250412_*.txt
```

### Legacy Documentation

Documentation specific to the legacy implementation that has been superseded by the clean architecture documentation:

```
INTERACTIVE_MENU.md
MULTI_VIEW.md
```

## Keeping the Compatibility Layer

Note that we're keeping the compatibility layer at `src/infrastructure/compatibility/` for now to ensure backward compatibility with any existing code that might still be referencing the legacy interfaces. This will be removed in a future phase once we're confident all references have been updated.

## Execution Plan

1. Create backups before removal
2. Remove the identified files and directories
3. Run the complete test suite to verify functionality
4. Update the documentation to reflect the changes

## Script for Removal

You can use the following script to remove the identified files and directories:

```python
import os
import shutil

# Base directories
root_dir = "."
src_dir = os.path.join(root_dir, "src")

# Directories to remove
directories_to_remove = [
    os.path.join(src_dir, "modules"),
    os.path.join(src_dir, "refactored")
]

# Files to remove from root directory
root_files_to_remove = [
    "zendesk_menu.py",
    "zendesk_menu.sh",
    "zendesk_menu.bat",
    "zendesk_ai_app.py",
    "zendesk_ai_app.bat"
]

# Files to remove from src directory
src_files_to_remove = [
    "ai_service.py",
    "analyze_and_update_ticket.py",
    "claude_enhanced_sentiment.py",
    "claude_service.py",
    "enhanced_sentiment.py",
    "mongodb_helper.py",
    "unified_ai_service.py",
    "unified_sentiment.py",
    "zendesk_ai_app.py"
]

# Temporary files to remove
temp_files_to_remove = [
    f for f in os.listdir(root_dir) if f.startswith(("dependency_graph_", "legacy_references_", "legacy_summary_", "import_update_report_"))
]

# Legacy documentation to remove
legacy_docs_to_remove = [
    "INTERACTIVE_MENU.md",
    "MULTI_VIEW.md"
]

# Create a log file
with open("cleanup_log.txt", "w") as log_file:
    # Remove directories
    for directory in directories_to_remove:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                log_file.write(f"Removed directory: {directory}\n")
                print(f"Removed directory: {directory}")
            except Exception as e:
                log_file.write(f"Error removing directory {directory}: {e}\n")
                print(f"Error removing directory {directory}: {e}")
    
    # Remove root files
    for file in root_files_to_remove:
        file_path = os.path.join(root_dir, file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                log_file.write(f"Removed file: {file_path}\n")
                print(f"Removed file: {file_path}")
            except Exception as e:
                log_file.write(f"Error removing file {file_path}: {e}\n")
                print(f"Error removing file {file_path}: {e}")
    
    # Remove src files
    for file in src_files_to_remove:
        file_path = os.path.join(src_dir, file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                log_file.write(f"Removed file: {file_path}\n")
                print(f"Removed file: {file_path}")
            except Exception as e:
                log_file.write(f"Error removing file {file_path}: {e}\n")
                print(f"Error removing file {file_path}: {e}")
    
    # Remove temporary files
    for file in temp_files_to_remove:
        file_path = os.path.join(root_dir, file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                log_file.write(f"Removed file: {file_path}\n")
                print(f"Removed file: {file_path}")
            except Exception as e:
                log_file.write(f"Error removing file {file_path}: {e}\n")
                print(f"Error removing file {file_path}: {e}")
    
    # Remove legacy documentation
    for file in legacy_docs_to_remove:
        file_path = os.path.join(root_dir, file)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                log_file.write(f"Removed file: {file_path}\n")
                print(f"Removed file: {file_path}")
            except Exception as e:
                log_file.write(f"Error removing file {file_path}: {e}\n")
                print(f"Error removing file {file_path}: {e}")

print("Cleanup completed. See cleanup_log.txt for details.")
```

## Next Steps

1. Update import statements in any remaining code to use the clean architecture components directly
2. Remove the compatibility layer once all references to legacy code are eliminated
3. Update documentation to reflect the new architecture
4. Consider adding more unit tests for the clean architecture components
