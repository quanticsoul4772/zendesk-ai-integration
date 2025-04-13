#!/usr/bin/env python3

"""
Zendesk AI Integration Cleanup Script

This script archives and removes files that are no longer needed after
the transition to Clean Architecture is complete.
"""

import os
import sys
import shutil
import logging
import datetime
import argparse
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cleanup_execution.log')
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
    archive_path = os.path.join(archive_dir, f"cleanup_{timestamp}")
    os.makedirs(archive_path)
    
    # Copy files to archive
    for file_path in files_to_archive:
        if os.path.exists(file_path):
            try:
                dest_path = os.path.join(archive_path, os.path.basename(file_path))
                if os.path.isdir(file_path):
                    # Copy directory
                    shutil.copytree(file_path, dest_path)
                else:
                    # Copy file
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
        "skipped": [],
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
            logger.warning(f"Path not found, skipping: {path}")
            summary["skipped"].append(path)
    
    return summary

def clear_test_results_directory(dry_run: bool = True) -> Tuple[int, List[str]]:
    """
    Clear the test_results directory but keep the directory itself.
    
    Args:
        dry_run: Whether to perform a dry run (no actual deletion)
        
    Returns:
        Tuple of (files_removed, failed_removals)
    """
    test_results_dir = "test_results"
    files_removed = 0
    failed_removals = []
    
    if os.path.exists(test_results_dir) and os.path.isdir(test_results_dir):
        for item in os.listdir(test_results_dir):
            item_path = os.path.join(test_results_dir, item)
            
            if not dry_run:
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                    logger.info(f"Removed test result: {item_path}")
                    files_removed += 1
                except Exception as e:
                    error_msg = f"Error removing {item_path}: {e}"
                    logger.error(error_msg)
                    failed_removals.append(item_path)
            else:
                logger.info(f"[DRY RUN] Would remove test result: {item_path}")
    else:
        logger.warning(f"Test results directory not found: {test_results_dir}")
    
    return files_removed, failed_removals

def main():
    """Execute the cleanup script."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Zendesk AI Integration Cleanup Script")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no files will be deleted)")
    parser.add_argument("--skip-archive", action="store_true", help="Skip creating an archive of files before removal")
    parser.add_argument("--clear-test-results", action="store_true", help="Clear the test_results directory")
    args = parser.parse_args()
    
    # Log script start
    logger.info("Starting Zendesk AI Integration cleanup script")
    if args.dry_run:
        logger.info("Performing dry run (no files will be deleted)")
    if args.skip_archive:
        logger.info("Skipping archive creation")
    
    # Files and directories to remove
    files_to_remove = [
        # Legacy CLI and Transition Files
        "zendesk_cli.py",
        "CLI_TRANSITION.md",
        "compare_cli.py",
        "simple_views.py",
        "show_commands.py",
        
        # Temporary Test Files
        "final_analyze_test.py",
        "final_test.py",
        "test_analyze.py",
        "test_analyze_view.py",
        "test_analyze_view_fix.py",
        "test_views.py",
        "test_download_logic.py",
        
        # Cleanup Scripts
        "final_cleanup.py",
        "final_cleanup.log",
        "remove_files.py",
        
        # Output/Report Files
        "hardware_report.html",
        "hardware_report_fixed.html",
        "hardware_report_test.html",
        "sentiment_analysis_report_20250411_1018.txt",
        "support_views_comparison.html",
        "support_views_report.txt",
        "multi_view_report.txt",
        
        # Enhancement and Implementation Scripts
        "improve_html_report.py",
        "future_implementation.py",
        "run_analyze.py",
        "zendesk.bat",
        
        # Deprecated Configuration
        ".env.fixed",
        "update_checksums.py",
        
        # Redundant Documentation
        "ENHANCEMENT_REPORT.md",
        "test_code_review_checklist.md",
        "test_optimization_guide.md",
        
        # Unused batch files
        "beautify_reports.bat"
    ]
    
    # Create archive if not skipped
    if not args.skip_archive:
        archive_path = create_archive(files_to_remove)
        logger.info(f"Created archive at {archive_path}")
    
    # Remove files and directories
    summary = remove_files_and_directories(files_to_remove, args.dry_run)
    
    # Clear test results directory if requested
    if args.clear_test_results:
        test_results_removed, test_results_failed = clear_test_results_directory(args.dry_run)
        summary["files_removed"] += test_results_removed
        summary["failed_removals"].extend(test_results_failed)
    
    # Print summary
    print("\nCleanup Summary:")
    print(f"- Files removed: {summary['files_removed']}")
    print(f"- Directories removed: {summary['directories_removed']}")
    
    # Print skipped files
    if summary["skipped"]:
        print("\nSkipped (not found):")
        for path in summary["skipped"]:
            print(f"- {path}")
    
    # Print failures
    if summary["failed_removals"]:
        print("\nFailed Removals:")
        for path in summary["failed_removals"]:
            print(f"- {path}")
    
    # Print success message
    if not args.dry_run:
        print("\nCleanup complete! The project has been tidied up and unnecessary files removed.")
    else:
        print("\nDry run complete. Run without --dry-run to perform actual cleanup.")
    
    # Log script end
    logger.info("Cleanup script completed")
    
    # Return success
    return 0

if __name__ == "__main__":
    sys.exit(main())
