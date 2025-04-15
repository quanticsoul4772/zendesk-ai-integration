#!/usr/bin/env python3

"""
Final Cleanup Script for Zendesk AI Integration

This script removes temporary files, logs, and transition scripts
that are no longer needed after completing the transition to clean architecture.
"""

import os
import sys
import shutil
import logging
import datetime
import argparse
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('final_cleanup.log')
    ]
)
logger = logging.getLogger(__name__)

def create_archive(files_to_archive: List[str], archive_dir: str = "archive") -> str:
    """
    Create an archive of files before removal.
    
    Args:
        files_to_archive: List of files to archive
        archive_dir: Directory to store archives
        
    Returns:
        Path to the archive directory
    """
    # Create archive directory if it doesn't exist
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    # Generate timestamp for archive name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate archive path
    archive_path = os.path.join(archive_dir, f"transition_files_{timestamp}")
    os.makedirs(archive_path)
    
    # Copy files to archive
    for file_path in files_to_archive:
        if os.path.exists(file_path):
            try:
                if os.path.isdir(file_path):
                    # Copy directory
                    dir_name = os.path.basename(file_path)
                    dest_path = os.path.join(archive_path, dir_name)
                    shutil.copytree(file_path, dest_path)
                else:
                    # Copy file
                    dest_path = os.path.join(archive_path, os.path.basename(file_path))
                    shutil.copy2(file_path, dest_path)
                
                logger.info(f"Archived {file_path} to {dest_path}")
            except Exception as e:
                logger.error(f"Error archiving {file_path}: {e}")
    
    return archive_path

def remove_files_and_directories(files_to_remove: List[str], dry_run: bool = True) -> Dict[str, Any]:
    """
    Remove specified files and directories.
    
    Args:
        files_to_remove: List of files and directories to remove
        dry_run: Whether to perform a dry run (no actual deletion)
        
    Returns:
        Summary dictionary
    """
    summary = {
        "files_removed": 0,
        "directories_removed": 0,
        "failed_removals": []
    }
    
    # Remove files and directories
    for path in files_to_remove:
        if os.path.exists(path):
            if not dry_run:
                try:
                    if os.path.isdir(path):
                        # Remove directory
                        shutil.rmtree(path)
                        logger.info(f"Removed directory: {path}")
                        summary["directories_removed"] += 1
                    else:
                        # Remove file
                        os.remove(path)
                        logger.info(f"Removed file: {path}")
                        summary["files_removed"] += 1
                except Exception as e:
                    error_msg = f"Error removing {path}: {e}"
                    logger.error(error_msg)
                    summary["failed_removals"].append(path)
            else:
                if os.path.isdir(path):
                    logger.info(f"[DRY RUN] Would remove directory: {path}")
                else:
                    logger.info(f"[DRY RUN] Would remove file: {path}")
        else:
            logger.warning(f"Path not found: {path}")
    
    return summary

def clean_pycache_directories(dry_run: bool = True) -> Dict[str, Any]:
    """
    Clean __pycache__ directories of legacy module references.
    
    Args:
        dry_run: Whether to perform a dry run (no actual deletion)
        
    Returns:
        Summary dictionary
    """
    summary = {
        "cache_files_removed": 0,
        "failed_removals": []
    }
    
    legacy_module_patterns = [
        "ai_service", 
        "claude_service", 
        "enhanced_sentiment",
        "claude_enhanced_sentiment", 
        "unified_ai_service",
        "unified_sentiment", 
        "zendesk_ai_app",
        "test_compatibility_adapters",
        "test_cli_legacy"
    ]
    
    # Walk through project directories
    for root, dirs, files in os.walk("."):
        # Skip venv directory
        if "venv" in root:
            continue
        
        # Check if this is a __pycache__ directory
        if os.path.basename(root) == "__pycache__":
            for file in files:
                # Check if file matches legacy module patterns
                if any(pattern in file for pattern in legacy_module_patterns):
                    file_path = os.path.join(root, file)
                    
                    if not dry_run:
                        try:
                            os.remove(file_path)
                            logger.info(f"Removed cache file: {file_path}")
                            summary["cache_files_removed"] += 1
                        except Exception as e:
                            error_msg = f"Error removing cache file {file_path}: {e}"
                            logger.error(error_msg)
                            summary["failed_removals"].append(file_path)
                    else:
                        logger.info(f"[DRY RUN] Would remove cache file: {file_path}")
    
    return summary

def main():
    """Run the final cleanup script."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Final Cleanup Script for Zendesk AI Integration")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no files will be deleted)")
    parser.add_argument("--skip-archive", action="store_true", help="Skip creating an archive of files before removal")
    parser.add_argument("--clean-backups", action="store_true", help="Also clean up backup files from previous steps")
    args = parser.parse_args()
    
    # Log script start
    logger.info("Starting final cleanup script")
    if args.dry_run:
        logger.info("Performing dry run (no files will be deleted)")
    if args.skip_archive:
        logger.info("Skipping archive creation")
    if args.clean_backups:
        logger.info("Will also clean up backup files")
    
    # Files and directories to remove
    files_to_remove = [
        # Cleanup and transition scripts
        "cleanup.py",
        "update_imports.py",
        "remove_compatibility.py",
        "fix_imports.py",
        
        # Temporary and log files
        "cleanup.log",
        "update_imports.log",
        "remove_compatibility.log",
        "legacy_removal_report_20250412_192249.txt",
        
        # Transition documentation files
        "CLEANUP_PLAN.md",
        "FINAL_CLEANUP.md",
        "CLEAN_ARCHITECTURE_COMPLETION.md",
        "LEGACY_REMOVAL_GUIDE.md",
        "LEGACY_REMOVAL_SUMMARY.md",
        "PHASE2_REMOVAL_PLAN.md",
    ]
    
    # Add backup directory if requested
    if args.clean_backups:
        files_to_remove.append("backups")
    
    # Create archive if not skipped
    if not args.skip_archive:
        archive_path = create_archive(files_to_remove)
        logger.info(f"Created archive at {archive_path}")
    
    # Remove files and directories
    summary = remove_files_and_directories(files_to_remove, args.dry_run)
    
    # Clean __pycache__ directories
    cache_summary = clean_pycache_directories(args.dry_run)
    
    # Combine summaries
    summary["cache_files_removed"] = cache_summary["cache_files_removed"]
    summary["failed_removals"].extend(cache_summary["failed_removals"])
    
    # Print summary
    print("\nCleanup Summary:")
    print(f"- Files removed: {summary['files_removed']}")
    print(f"- Directories removed: {summary['directories_removed']}")
    print(f"- Cache files removed: {summary['cache_files_removed']}")
    
    # Print failures
    if summary["failed_removals"]:
        print("\nFailed Removals:")
        for path in summary["failed_removals"]:
            print(f"- {path}")
    
    # Print success message
    if not args.dry_run:
        print("\nFinal cleanup complete! The project is now fully transitioned to clean architecture.")
    else:
        print("\nDry run complete. Run without --dry-run to perform actual cleanup.")
    
    # Log script end
    logger.info("Final cleanup script completed")
    
    # Return success
    return 0

if __name__ == "__main__":
    sys.exit(main())
