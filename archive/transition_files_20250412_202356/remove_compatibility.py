#!/usr/bin/env python3

"""
Remove Compatibility Layer Script for Zendesk AI Integration

This script removes the compatibility layer after all references have been updated
to use the clean architecture components directly.
"""

import os
import sys
import shutil
import logging
import datetime
import argparse
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('remove_compatibility.log')
    ]
)
logger = logging.getLogger(__name__)

def check_for_references() -> bool:
    """
    Check if there are any remaining references to the compatibility layer.
    
    Returns:
        True if references found, False otherwise
    """
    # Check if update_imports.py has been run
    if not os.path.exists("update_imports.log"):
        logger.warning("update_imports.py has not been run. Please run it first to identify and update references.")
        return True
    
    # Check update_imports.log for references
    with open("update_imports.log", "r") as f:
        log_content = f.read()
        if "Found references to compatibility layer" in log_content:
            last_run_index = log_content.rfind("Starting update imports script")
            if last_run_index >= 0:
                # Check if there are references after the last run
                last_log = log_content[last_run_index:]
                if "Found 0 files with references" not in last_log:
                    logger.warning("update_imports.py found references to the compatibility layer.")
                    logger.warning("Please run update_imports.py without --dry-run to update those references.")
                    return True
    
    return False

def create_backup(compatibility_dir: str, backup_dir: str = "backups") -> str:
    """
    Create a backup of the compatibility layer.
    
    Args:
        compatibility_dir: Path to the compatibility layer
        backup_dir: Directory to store backups
        
    Returns:
        Path to the backup
    """
    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Generate timestamp for backup name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate backup path
    backup_name = f"compatibility_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Create backup
    try:
        # Copy directory
        shutil.copytree(compatibility_dir, backup_path)
        logger.info(f"Created backup of compatibility layer at {backup_path}")
        
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return ""

def remove_compatibility_layer(compatibility_dir: str, test_file: str, backup_path: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Remove the compatibility layer and test file.
    
    Args:
        compatibility_dir: Path to the compatibility layer
        test_file: Path to the compatibility test file
        backup_path: Path to the backup
        dry_run: Whether to perform a dry run (no actual removal)
        
    Returns:
        Summary dictionary
    """
    summary = {
        "compatibility_dir_removed": False,
        "test_file_removed": False,
        "backup_created": bool(backup_path)
    }
    
    # Remove compatibility layer
    if os.path.exists(compatibility_dir):
        if not dry_run:
            try:
                shutil.rmtree(compatibility_dir)
                logger.info(f"Removed compatibility layer at {compatibility_dir}")
                summary["compatibility_dir_removed"] = True
            except Exception as e:
                logger.error(f"Error removing compatibility layer: {e}")
        else:
            logger.info(f"[DRY RUN] Would remove compatibility layer at {compatibility_dir}")
    else:
        logger.warning(f"Compatibility layer not found at {compatibility_dir}")
    
    # Remove compatibility test file
    if os.path.exists(test_file):
        if not dry_run:
            try:
                # Copy test file to backup dir if not already done
                if backup_path and not os.path.exists(os.path.join(backup_path, os.path.basename(test_file))):
                    shutil.copy2(test_file, os.path.join(backup_path, os.path.basename(test_file)))
                    logger.info(f"Created backup of test file at {os.path.join(backup_path, os.path.basename(test_file))}")
                
                # Remove test file
                os.remove(test_file)
                logger.info(f"Removed test file at {test_file}")
                summary["test_file_removed"] = True
            except Exception as e:
                logger.error(f"Error removing test file: {e}")
        else:
            logger.info(f"[DRY RUN] Would remove test file at {test_file}")
    else:
        logger.warning(f"Test file not found at {test_file}")
    
    return summary

def main():
    """Run the remove compatibility layer script."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Remove Compatibility Layer Script for Zendesk AI Integration")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no files will be deleted)")
    parser.add_argument("--force", action="store_true", help="Force removal even if references might exist")
    args = parser.parse_args()
    
    # Log script start
    logger.info("Starting remove compatibility layer script")
    if args.dry_run:
        logger.info("Performing dry run (no files will be deleted)")
    if args.force:
        logger.info("Forcing removal even if references might exist")
    
    # Paths
    compatibility_dir = "src/infrastructure/compatibility"
    test_file = "tests/unit/test_compatibility_adapters.py"
    
    # Check for references unless forced
    if not args.force and check_for_references():
        logger.error("Cannot remove compatibility layer while references exist.")
        logger.error("Please update all references first or use --force to override.")
        return 1
    
    # Create backup
    backup_path = create_backup(compatibility_dir) if os.path.exists(compatibility_dir) else ""
    
    # Remove compatibility layer
    summary = remove_compatibility_layer(compatibility_dir, test_file, backup_path, args.dry_run)
    
    # Print summary
    print("\nRemoval Summary:")
    print(f"- Compatibility directory removed: {summary['compatibility_dir_removed']}")
    print(f"- Test file removed: {summary['test_file_removed']}")
    print(f"- Backup created: {summary['backup_created']}")
    
    # Print next steps
    print("\nNext Steps:")
    print("1. Run the test suite to ensure everything passes:")
    print("   pytest")
    print("2. Verify the application works correctly without the compatibility layer")
    print("3. Update any documentation that might reference the compatibility layer")
    
    # Log script end
    logger.info("Remove compatibility layer script completed")
    
    # Return success
    return 0

if __name__ == "__main__":
    sys.exit(main())
