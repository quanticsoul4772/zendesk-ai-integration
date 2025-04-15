#!/usr/bin/env python3
"""
Legacy Files Removal Script

This script removes legacy files from the codebase after they have been
replaced with compatibility adapters.

Usage:
    python remove_legacy_files.py [--dry-run]
"""

import os
import shutil
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("remove_legacy")

# Define legacy components to remove
LEGACY_FILES = [
    "src/modules/ai_analyzer.py",
    "src/modules/cache_manager.py",
    "src/modules/db_repository.py",
    "src/modules/report_generator.py",
    "src/modules/scheduler.py",
    "src/modules/webhook_server.py",
    "src/modules/zendesk_client.py",
    "src/infrastructure/utils/service_provider.py",
]

LEGACY_DIRS = [
    "src/modules/reporters",
]

def remove_legacy_files(root_dir, dry_run=False):
    """
    Remove legacy files and directories.
    
    Args:
        root_dir: Root directory of the project
        dry_run: Whether to simulate the removal without making changes
        
    Returns:
        Tuple of (files_removed, dirs_removed, errors)
    """
    files_removed = []
    dirs_removed = []
    errors = []
    
    # Remove files
    for file_path in LEGACY_FILES:
        full_path = os.path.join(root_dir, file_path)
        if os.path.exists(full_path):
            try:
                if not dry_run:
                    os.remove(full_path)
                files_removed.append(file_path)
                logger.info(f"{'Would remove' if dry_run else 'Removed'} file: {file_path}")
            except Exception as e:
                errors.append((file_path, str(e)))
                logger.error(f"Error removing file {file_path}: {e}")
        else:
            logger.warning(f"File not found: {file_path}")
    
    # Remove directories
    for dir_path in LEGACY_DIRS:
        full_path = os.path.join(root_dir, dir_path)
        if os.path.exists(full_path):
            try:
                if not dry_run:
                    shutil.rmtree(full_path)
                dirs_removed.append(dir_path)
                logger.info(f"{'Would remove' if dry_run else 'Removed'} directory: {dir_path}")
            except Exception as e:
                errors.append((dir_path, str(e)))
                logger.error(f"Error removing directory {dir_path}: {e}")
        else:
            logger.warning(f"Directory not found: {dir_path}")
    
    return files_removed, dirs_removed, errors

def main():
    parser = argparse.ArgumentParser(description="Remove legacy files from the codebase")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the removal without making changes")
    parser.add_argument("--root-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      help="Root directory of the project")
    args = parser.parse_args()
    
    logger.info(f"Starting legacy file removal in {args.root_dir}" + (" (dry run)" if args.dry_run else ""))
    
    # Confirm before proceeding
    if not args.dry_run:
        confirmation = input("This will permanently remove legacy files. Have you backed up the files? (y/n): ")
        if confirmation.lower() != 'y':
            logger.info("Aborted. No files were removed.")
            return
    
    files_removed, dirs_removed, errors = remove_legacy_files(args.root_dir, args.dry_run)
    
    logger.info(f"Legacy file removal complete:")
    logger.info(f"  Files removed: {len(files_removed)}")
    logger.info(f"  Directories removed: {len(dirs_removed)}")
    
    if errors:
        logger.warning(f"  Errors encountered: {len(errors)}")
        for path, error in errors:
            logger.warning(f"    - {path}: {error}")
    
    # Generate a report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(args.root_dir, f"legacy_removal_report_{timestamp}.txt")
    
    with open(report_path, "w", encoding="utf-8") as report:
        report.write("Legacy File Removal Report\n")
        report.write("=========================\n\n")
        report.write(f"Timestamp: {datetime.now()}\n")
        report.write(f"Mode: {'Dry run (no changes made)' if args.dry_run else 'Live removal'}\n\n")
        
        report.write(f"Files removed: {len(files_removed)}\n")
        for file_path in files_removed:
            report.write(f"  - {file_path}\n")
        
        report.write(f"\nDirectories removed: {len(dirs_removed)}\n")
        for dir_path in dirs_removed:
            report.write(f"  - {dir_path}\n")
        
        if errors:
            report.write(f"\nErrors encountered: {len(errors)}\n")
            for path, error in errors:
                report.write(f"  - {path}: {error}\n")
        else:
            report.write("\nNo errors encountered.\n")
    
    logger.info(f"Report written to {report_path}")

if __name__ == "__main__":
    main()
