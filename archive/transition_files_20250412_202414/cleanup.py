#!/usr/bin/env python3

"""
Cleanup Script for Zendesk AI Integration

This script removes legacy files and directories that are no longer needed after
the transition to clean architecture.
"""

import os
import shutil
import argparse
import datetime
import logging
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup.log')
    ]
)
logger = logging.getLogger(__name__)


def create_backup(path: str, backup_dir: str = "backups") -> str:
    """
    Create a backup of a file or directory.
    
    Args:
        path: Path to the file or directory to backup
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
    basename = os.path.basename(path)
    backup_name = f"{basename}_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Create backup
    try:
        if os.path.isdir(path):
            # Copy directory
            shutil.copytree(path, backup_path)
            logger.info(f"Created backup of directory {path} at {backup_path}")
        else:
            # Copy file
            shutil.copy2(path, backup_path)
            logger.info(f"Created backup of file {path} at {backup_path}")
        
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup of {path}: {e}")
        return ""


def remove_files_and_directories(
    directories: List[str],
    root_files: List[str],
    src_files: List[str],
    temp_files: List[str],
    docs_files: List[str],
    dry_run: bool = True,
    create_backups: bool = True
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Remove files and directories.
    
    Args:
        directories: List of directories to remove
        root_files: List of files in the root directory to remove
        src_files: List of files in the src directory to remove
        temp_files: List of temporary files to remove
        docs_files: List of documentation files to remove
        dry_run: Whether to perform a dry run (no actual deletion)
        create_backups: Whether to create backups before removal
        
    Returns:
        Tuple of (summary dictionary, error list)
    """
    # Base directories
    root_dir = "."
    src_dir = os.path.join(root_dir, "src")
    
    # Summary
    summary = {
        "directories_removed": 0,
        "root_files_removed": 0,
        "src_files_removed": 0,
        "temp_files_removed": 0,
        "docs_files_removed": 0,
        "backups_created": 0
    }
    
    # Error list
    errors = []
    
    # Remove directories
    for directory in directories:
        directory_path = os.path.join(src_dir, directory)
        if os.path.exists(directory_path):
            # Create backup if requested
            if create_backups:
                backup_path = create_backup(directory_path)
                if backup_path:
                    summary["backups_created"] += 1
            
            # Remove directory
            if not dry_run:
                try:
                    shutil.rmtree(directory_path)
                    logger.info(f"Removed directory: {directory_path}")
                    summary["directories_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing directory {directory_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.info(f"[DRY RUN] Would remove directory: {directory_path}")
    
    # Remove root files
    for file in root_files:
        file_path = os.path.join(root_dir, file)
        if os.path.exists(file_path):
            # Create backup if requested
            if create_backups:
                backup_path = create_backup(file_path)
                if backup_path:
                    summary["backups_created"] += 1
            
            # Remove file
            if not dry_run:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                    summary["root_files_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing file {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.info(f"[DRY RUN] Would remove file: {file_path}")
    
    # Remove src files
    for file in src_files:
        file_path = os.path.join(src_dir, file)
        if os.path.exists(file_path):
            # Create backup if requested
            if create_backups:
                backup_path = create_backup(file_path)
                if backup_path:
                    summary["backups_created"] += 1
            
            # Remove file
            if not dry_run:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                    summary["src_files_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing file {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.info(f"[DRY RUN] Would remove file: {file_path}")
    
    # Remove temporary files
    for file_pattern in temp_files:
        # Find matching files
        matching_files = [f for f in os.listdir(root_dir) if f.startswith(file_pattern)]
        
        for file in matching_files:
            file_path = os.path.join(root_dir, file)
            
            # Create backup if requested
            if create_backups:
                backup_path = create_backup(file_path)
                if backup_path:
                    summary["backups_created"] += 1
            
            # Remove file
            if not dry_run:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                    summary["temp_files_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing file {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.info(f"[DRY RUN] Would remove file: {file_path}")
    
    # Remove documentation files
    for file in docs_files:
        file_path = os.path.join(root_dir, file)
        if os.path.exists(file_path):
            # Create backup if requested
            if create_backups:
                backup_path = create_backup(file_path)
                if backup_path:
                    summary["backups_created"] += 1
            
            # Remove file
            if not dry_run:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed file: {file_path}")
                    summary["docs_files_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing file {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            else:
                logger.info(f"[DRY RUN] Would remove file: {file_path}")
    
    return summary, errors


def main():
    """Run the cleanup script."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Cleanup script for Zendesk AI Integration")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no files will be deleted)")
    parser.add_argument("--no-backups", action="store_true", help="Do not create backups before removal")
    args = parser.parse_args()
    
    # Log script start
    logger.info("Starting cleanup script")
    if args.dry_run:
        logger.info("Performing dry run (no files will be deleted)")
    if args.no_backups:
        logger.info("Backups disabled")
    
    # Directories to remove (relative to src/)
    directories = [
        "modules",
        "refactored"
    ]
    
    # Files to remove from root directory
    root_files = [
        "zendesk_menu.py",
        "zendesk_menu.sh",
        "zendesk_menu.bat",
        "zendesk_ai_app.py",
        "zendesk_ai_app.bat"
    ]
    
    # Files to remove from src directory
    src_files = [
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
    
    # Temporary file patterns to remove
    temp_files = [
        "dependency_graph_",
        "legacy_references_",
        "legacy_summary_",
        "import_update_report_"
    ]
    
    # Legacy documentation to remove
    docs_files = [
        "INTERACTIVE_MENU.md",
        "MULTI_VIEW.md"
    ]
    
    # Remove files and directories
    summary, errors = remove_files_and_directories(
        directories=directories,
        root_files=root_files,
        src_files=src_files,
        temp_files=temp_files,
        docs_files=docs_files,
        dry_run=args.dry_run,
        create_backups=not args.no_backups
    )
    
    # Print summary
    print("\nCleanup Summary:")
    print(f"- Directories removed: {summary['directories_removed']}")
    print(f"- Root files removed: {summary['root_files_removed']}")
    print(f"- Src files removed: {summary['src_files_removed']}")
    print(f"- Temporary files removed: {summary['temp_files_removed']}")
    print(f"- Documentation files removed: {summary['docs_files_removed']}")
    print(f"- Backups created: {summary['backups_created']}")
    
    # Print errors
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
    
    # Log script end
    logger.info("Cleanup script completed")
    
    # Return success if no errors
    return 0 if not errors else 1


if __name__ == "__main__":
    main()
