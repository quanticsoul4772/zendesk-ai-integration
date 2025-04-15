# Clean Architecture Transition Guide

## Current Status

The project is currently in a transition phase from the legacy implementation to the new clean architecture implementation. This document explains the current state, issues identified, and the temporary solution we've put in place.

## Issue Overview

During the transition to the clean architecture, we encountered the following issues:

1. **Import Path Issues**: The clean architecture implementation used absolute imports from the project root (e.g., `from infrastructure.utils.service_provider import ServiceProvider`) which caused "ModuleNotFoundError" when running the application.

2. **Command Registration Issues**: The `name` and `description` properties in command classes were being accessed directly as class attributes, but they're defined as properties that can only be accessed from an instance.

3. **Command Line Argument Parsing**: The new architecture uses a different command-line interface pattern (subcommands instead of `--mode`) which broke backward compatibility with existing scripts and documentation.

## Solutions Implemented

### 1. Import Path Fixes

The import path issues were fixed by modifying the import statements in the clean architecture implementation to use the `src.` prefix for absolute imports:

```python
# Before
from infrastructure.utils.service_provider import ServiceProvider

# After
from src.infrastructure.utils.service_provider import ServiceProvider
```

We created a script (`fix_imports.py`) that automatically updates these imports across the codebase. This script updated 48 files with the correct import paths.

### 2. Command Registration Fix

To fix the command registration issues, we updated the `register_command` method in the `CommandHandler` class to properly handle property access from both class attributes and instance attributes:

```python
def register_command(self, command_class: Type[Command]) -> None:
    # Create temporary instance to get name and description if needed
    command_instance = None
    
    # Get command name
    try:
        # Try to get name directly from class
        command_name = command_class.name
        if callable(command_name):
            # If it's a method, we need an instance
            if not command_instance:
                command_instance = command_class({}, None)
            command_name = command_instance.name
    except (AttributeError, TypeError):
        # Create an instance and get the name
        if not command_instance:
            command_instance = command_class({}, None)
        command_name = command_instance.name
    
    # Similar code for description...
    
    # Create a subparser for the command
    subparser = self.subparsers.add_parser(command_name, help=command_description)
```

### 3. Legacy Mode Compatibility

To maintain backward compatibility with the `--mode` argument pattern, we added code to map legacy modes to the new command names:

```python
def map_legacy_mode_to_command(args: List[str], legacy_mode: str) -> List[str]:
    # Define the mapping from legacy modes to new commands
    mode_to_command = {
        "list-views": "views",
        "run": "analyze",
        "webhook": "webhook",
        "schedule": "schedule",
        "sentiment": "report",
        "pending": "report",
        "multi-view": "report",
        "interactive": "interactive"
    }
    
    # Map the mode to the command
    command = mode_to_command.get(legacy_mode)
    if not command:
        return args
    
    # Create a new argument list with the command
    new_args = [command]
    
    # Append all other arguments except --mode
    for i in range(len(args)):
        if args[i] == "--mode":
            # Skip the --mode argument and its value
            i += 1
        else:
            new_args.append(args[i])
    
    return new_args
```

## Temporary Solution

While the clean architecture implementation is being finalized, we've created a temporary solution that maintains full backward compatibility:

1. **Temporary CLI Script**: We created a `zendesk_cli.py` script that uses the legacy implementation from `src/modules/` while displaying a notice that this is a temporary solution.

2. **Convenience Batch File**: A `zendesk.bat` file was created for Windows users to easily run the temporary CLI script.

3. **Updated Menu Script**: The `zendesk_menu.py` script was updated to use the temporary CLI script for launching the interactive menu.

## Completing the Transition

To complete the transition to the clean architecture implementation, the following steps need to be taken:

1. **Fix Command Registration**: Complete the fixes for command registration to properly handle property access and ensure command names are correctly registered.

2. **Update Command Classes**: Make sure all command classes properly implement the `name` and `description` properties.

3. **Update Documentation**: Update all documentation to reflect the new command-line interface pattern once it's fully implemented.

4. **Remove Legacy Implementation**: Once the clean architecture implementation is complete and tested, the legacy implementation and temporary scripts can be removed.

## Recommended Development Approach

For ongoing development during this transition period, we recommend:

1. **Use Temporary CLI**: Use the temporary CLI script (`zendesk_cli.py`) for running the application.

2. **Update Both Implementations**: When making changes, update both the legacy implementation and the clean architecture implementation.

3. **Test Thoroughly**: Test both implementations to ensure they work correctly.

4. **Prioritize Clean Architecture**: Focus development efforts on completing the clean architecture implementation.

## Timeline

The clean architecture implementation should be completed within the next sprint cycle. The temporary solution will be maintained until then to ensure uninterrupted usage of the application.
