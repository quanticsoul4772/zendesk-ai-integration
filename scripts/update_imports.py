#!/usr/bin/env python3
"""
Import Updater Script

This script updates import statements in the codebase to use the compatibility adapters
instead of directly importing legacy components.

Usage:
    python update_imports.py [--dry-run]
"""

import os
import re
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_imports")

# Mapping of legacy imports to compatibility layer imports
IMPORT_MAPPINGS = {
    # ZendeskClient
    r'from src\.modules\.zendesk_client import ZendeskClient': 
        'from src.infrastructure.compatibility import ZendeskClient',
    r'from modules\.zendesk_client import ZendeskClient': 
        'from src.infrastructure.compatibility import ZendeskClient',
    
    # AIAnalyzer
    r'from src\.modules\.ai_analyzer import AIAnalyzer': 
        'from src.infrastructure.compatibility import AIAnalyzer',
    r'from modules\.ai_analyzer import AIAnalyzer': 
        'from src.infrastructure.compatibility import AIAnalyzer',
    
    # DBRepository
    r'from src\.modules\.db_repository import DBRepository': 
        'from src.infrastructure.compatibility import DBRepository',
    r'from modules\.db_repository import DBRepository': 
        'from src.infrastructure.compatibility import DBRepository',
    
    # WebhookServer
    r'from src\.modules\.webhook_server import WebhookServer': 
        'from src.infrastructure.compatibility import WebhookServer',
    r'from modules\.webhook_server import WebhookServer': 
        'from src.infrastructure.compatibility import WebhookServer',
    
    # Scheduler/TaskScheduler
    r'from src\.modules\.scheduler import (?:Scheduler|TaskScheduler)': 
        'from src.infrastructure.compatibility import Scheduler',
    r'from modules\.scheduler import (?:Scheduler|TaskScheduler)': 
        'from src.infrastructure.compatibility import Scheduler',
    
    # Reporters
    r'from src\.modules\.reporters\.sentiment_report import SentimentReporter': 
        'from src.infrastructure.compatibility import SentimentReporter',
    r'from modules\.reporters\.sentiment_report import SentimentReporter': 
        'from src.infrastructure.compatibility import SentimentReporter',
    
    r'from src\.modules\.reporters\.hardware_report import HardwareReporter': 
        'from src.infrastructure.compatibility import HardwareReporter',
    r'from modules\.reporters\.hardware_report import HardwareReporter': 
        'from src.infrastructure.compatibility import HardwareReporter',
    
    r'from src\.modules\.reporters\.pending_report import PendingReporter': 
        'from src.infrastructure.compatibility import PendingReporter',
    r'from modules\.reporters\.pending_report import PendingReporter': 
        'from src.infrastructure.compatibility import PendingReporter',
    
    # ServiceProvider
    r'from src\.infrastructure\.utils\.service_provider import ServiceProvider': 
        'from src.infrastructure.compatibility import ServiceProvider',
    r'from infrastructure\.utils\.service_provider import ServiceProvider': 
        'from src.infrastructure.compatibility import ServiceProvider',
    
    # report_generator functions
    r'from src\.modules\.report_generator import generate_summary_report': 
        'from src.infrastructure.compatibility import generate_summary_report',
    r'from modules\.report_generator import generate_summary_report': 
        'from src.infrastructure.compatibility import generate_summary_report',
    
    r'from src\.modules\.report_generator import generate_enhanced_summary_report': 
        'from src.infrastructure.compatibility import generate_enhanced_summary_report',
    r'from modules\.report_generator import generate_enhanced_summary_report': 
        'from src.infrastructure.compatibility import generate_enhanced_summary_report',
    
    r'from src\.modules\.report_generator import generate_hardware_report': 
        'from src.infrastructure.compatibility import generate_hardware_report',
    r'from modules\.report_generator import generate_hardware_report': 
        'from src.infrastructure.compatibility import generate_hardware_report',
    
    r'from src\.modules\.report_generator import generate_pending_report': 
        'from src.infrastructure.compatibility import generate_pending_report',
    r'from modules\.report_generator import generate_pending_report': 
        'from src.infrastructure.compatibility import generate_pending_report',
}

# Directories to ignore
IGNORE_DIRS = [
    ".git",
    "__pycache__",
    "venv",
    "backups",
    "node_modules",
]

def update_imports_in_file(file_path, dry_run=False):
    """
    Update imports in a single file.
    
    Args:
        file_path: Path to the file to update
        dry_run: Whether to simulate the update without making changes
        
    Returns:
        Tuple of (success, changes_made, errors)
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Track changes
        original_content = content
        changes_made = 0
        
        # Apply each import mapping
        for old_pattern, new_import in IMPORT_MAPPINGS.items():
            # Count matches
            matches = re.findall(old_pattern, content)
            changes_made += len(matches)
            
            # Replace the import statement
            content = re.sub(old_pattern, new_import, content)
        
        # Write back if changes were made and not in dry run mode
        if content != original_content and not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Updated {changes_made} imports in {file_path}")
        elif content != original_content:
            logger.info(f"Would update {changes_made} imports in {file_path} (dry run)")
        
        return True, changes_made, None
    
    except Exception as e:
        logger.error(f"Error updating {file_path}: {e}")
        return False, 0, str(e)

def update_imports_in_directory(directory, dry_run=False):
    """
    Update imports in all Python files in a directory and its subdirectories.
    
    Args:
        directory: Root directory to process
        dry_run: Whether to simulate the update without making changes
        
    Returns:
        Tuple of (files_processed, files_updated, total_changes, errors)
    """
    files_processed = 0
    files_updated = 0
    total_changes = 0
    errors = []
    
    for root, dirs, files in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        # Skip directories containing 'backups'
        if "backups" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                files_processed += 1
                
                success, changes, error = update_imports_in_file(file_path, dry_run)
                
                if success and changes > 0:
                    files_updated += 1
                    total_changes += changes
                
                if error:
                    errors.append((file_path, error))
    
    return files_processed, files_updated, total_changes, errors

def main():
    parser = argparse.ArgumentParser(description="Update legacy imports to use compatibility adapters")
    parser.add_argument("--dry-run", action="store_true", help="Simulate the update without making changes")
    parser.add_argument("--root-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      help="Root directory of the codebase to update")
    args = parser.parse_args()
    
    logger.info(f"Starting import update in {args.root_dir}" + (" (dry run)" if args.dry_run else ""))
    
    files_processed, files_updated, total_changes, errors = update_imports_in_directory(
        args.root_dir, args.dry_run
    )
    
    logger.info(f"Import update complete:")
    logger.info(f"  Files processed: {files_processed}")
    logger.info(f"  Files updated: {files_updated}")
    logger.info(f"  Total import statements updated: {total_changes}")
    
    if errors:
        logger.warning(f"  Errors encountered: {len(errors)}")
        for file_path, error in errors:
            logger.warning(f"    - {file_path}: {error}")
    
    # Generate a report file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(args.root_dir, f"import_update_report_{timestamp}.txt")
    
    with open(report_path, "w", encoding="utf-8") as report:
        report.write("Import Update Report\n")
        report.write("===================\n\n")
        report.write(f"Timestamp: {datetime.now()}\n")
        report.write(f"Mode: {'Dry run (no changes made)' if args.dry_run else 'Live update'}\n\n")
        
        report.write(f"Files processed: {files_processed}\n")
        report.write(f"Files updated: {files_updated}\n")
        report.write(f"Total import statements updated: {total_changes}\n\n")
        
        if errors:
            report.write(f"Errors encountered: {len(errors)}\n")
            for file_path, error in errors:
                report.write(f"  - {file_path}: {error}\n")
        else:
            report.write("No errors encountered.\n")
    
    logger.info(f"Report written to {report_path}")

if __name__ == "__main__":
    main()
