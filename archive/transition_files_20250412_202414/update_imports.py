#!/usr/bin/env python3

"""
Update Imports Script for Zendesk AI Integration

This script identifies and updates any references to the compatibility layer
to use the clean architecture components directly.
"""

import os
import re
import argparse
import logging
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_imports.log')
    ]
)
logger = logging.getLogger(__name__)

# Define patterns to search for
IMPORT_PATTERNS = [
    r'from src\.infrastructure\.compatibility\.(.*?) import (.*)',
    r'from src\.infrastructure\.compatibility import (.*)',
    r'import src\.infrastructure\.compatibility\.(.*)',
    r'import src\.infrastructure\.compatibility'
]

# Define replacement mappings
# Format: (old_import, new_import)
REPLACEMENT_MAPPINGS = {
    'ZendeskClient': 'from src.infrastructure.repositories.zendesk_repository import ZendeskRepository',
    'AIAnalyzer': 'from src.application.services.ticket_analysis_service import TicketAnalysisService',
    'DBRepository': 'from src.infrastructure.repositories.mongodb_repository import MongoDBRepository',
    'WebhookServer': 'from src.presentation.webhook.webhook_handler import WebhookHandler',
    'Scheduler': 'from src.infrastructure.external_services.scheduler_service import SchedulerService',
    'SentimentReporter': 'from src.application.services.report_service import SentimentReportService',
    'HardwareReporter': 'from src.application.services.report_service import HardwareReportService',
    'PendingReporter': 'from src.application.services.report_service import PendingReportService',
    'ServiceProvider': 'from src.infrastructure.service_provider import ServiceProvider',
    'generate_summary_report': 'from src.application.use_cases.generate_report_use_case import GenerateReportUseCase',
    'generate_enhanced_summary_report': 'from src.application.use_cases.generate_report_use_case import GenerateReportUseCase',
    'generate_hardware_report': 'from src.application.use_cases.generate_report_use_case import GenerateReportUseCase',
    'generate_pending_report': 'from src.application.use_cases.generate_report_use_case import GenerateReportUseCase',
}

# Define method mappings for converting compatibility calls to new architecture
METHOD_MAPPINGS = {
    # ZendeskClient to ZendeskRepository
    r'\.fetch_tickets\(': '.get_tickets(',
    r'\.fetch_tickets_from_view\(': '.get_tickets_from_view(',
    r'\.add_comment\(': '.add_comment(',
    r'\.update_ticket\(': '.update_ticket(',
    
    # AIAnalyzer to TicketAnalysisService
    r'\.analyze_ticket\(': '.analyze_ticket(',
    r'\.analyze_tickets_batch\(': '.analyze_tickets_batch(',
    
    # ServiceProvider conversions
    r'\.get_zendesk_client\(': '.get(ZendeskRepository)',
    r'\.get_ai_analyzer\(': '.get(TicketAnalysisService)',
    r'\.get_db_repository\(': '.get(MongoDBRepository)',
    
    # Report generation functions
    r'generate_summary_report\(': 'generate_report_use_case.execute(',
    r'generate_enhanced_summary_report\(': 'generate_report_use_case.execute(',
    r'generate_hardware_report\(': 'generate_report_use_case.execute(',
    r'generate_pending_report\(': 'generate_report_use_case.execute(',
}


def find_compatibility_references(directories: List[str]) -> Dict[str, List[Tuple[int, str]]]:
    """
    Find references to compatibility layer in the specified directories.
    
    Args:
        directories: List of directories to search
        
    Returns:
        Dictionary mapping file paths to lines with references
    """
    references = {}
    
    # Python file extensions to scan
    extensions = ['.py']
    
    # Process each directory
    for directory in directories:
        logger.info(f"Scanning directory: {directory}")
        
        # Walk through the directory
        for root, _, files in os.walk(directory):
            # Skip __pycache__ directories
            if '__pycache__' in root:
                continue
            
            # Skip the compatibility directory itself
            if 'compatibility' in root:
                continue
            
            # Process each file
            for file in files:
                # Check file extension
                if not any(file.endswith(ext) for ext in extensions):
                    continue
                
                # Get full file path
                file_path = os.path.join(root, file)
                
                # Process the file
                file_references = find_references_in_file(file_path)
                
                # Add to references if any found
                if file_references:
                    references[file_path] = file_references
    
    return references


def find_references_in_file(file_path: str) -> List[Tuple[int, str]]:
    """
    Find references to compatibility layer in the specified file.
    
    Args:
        file_path: Path to the file to search
        
    Returns:
        List of (line number, line content) tuples with references
    """
    references = []
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Process each line
        for i, line in enumerate(lines):
            # Check for import patterns
            for pattern in IMPORT_PATTERNS:
                if re.search(pattern, line):
                    references.append((i + 1, line.strip()))
                    break
            
            # Check for class and function usage
            for class_name in REPLACEMENT_MAPPINGS.keys():
                # Look for instances of the class name used directly
                if re.search(r'\b' + class_name + r'\b', line):
                    references.append((i + 1, line.strip()))
                    break
        
        return references
    
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return []


def update_file(file_path: str, dry_run: bool = True) -> Tuple[int, int, Dict[str, Any]]:
    """
    Update references to compatibility layer in the specified file.
    
    Args:
        file_path: Path to the file to update
        dry_run: Whether to perform a dry run (no actual changes)
        
    Returns:
        Tuple of (lines_checked, lines_updated, updates)
    """
    lines_checked = 0
    lines_updated = 0
    updates = {}
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Track if the file was modified
        modified = False
        
        # Track new imports to add
        new_imports = set()
        
        # Process each line
        for i, line in enumerate(lines):
            lines_checked += 1
            original_line = line
            
            # Check for import patterns
            for pattern in IMPORT_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    # Extract imported classes
                    if len(match.groups()) > 0:
                        for class_name in re.split(r',\s*', match.group(1)):
                            clean_class_name = class_name.strip()
                            if clean_class_name in REPLACEMENT_MAPPINGS:
                                new_imports.add(REPLACEMENT_MAPPINGS[clean_class_name])
                    
                    # Comment out the old import
                    line = f"# {line}"
                    modified = True
                    lines_updated += 1
                    break
            
            # Check for method usage patterns
            for old_pattern, new_pattern in METHOD_MAPPINGS.items():
                if re.search(old_pattern, line):
                    # Replace the method call
                    line = re.sub(old_pattern, new_pattern, line)
                    modified = True
                    lines_updated += 1
            
            # Update the line if modified
            if line != original_line:
                lines[i] = line
                updates[i + 1] = {'old': original_line.strip(), 'new': line.strip()}
        
        # Add new imports at the beginning of the file
        if new_imports:
            # Find where to insert new imports (after existing imports)
            last_import_line = 0
            for i, line in enumerate(lines):
                if re.match(r'^import|^from', line):
                    last_import_line = i + 1
            
            # Insert new imports
            for new_import in sorted(new_imports):
                lines.insert(last_import_line, f"{new_import}\n")
                last_import_line += 1
                lines_updated += 1
                updates[last_import_line] = {'old': '', 'new': new_import}
        
        # Write the updated file
        if modified and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logger.info(f"Updated file: {file_path}")
        
        return lines_checked, lines_updated, updates
    
    except Exception as e:
        logger.error(f"Error updating file {file_path}: {e}")
        return lines_checked, lines_updated, updates


def update_compatibility_references(directories: List[str], dry_run: bool = True) -> Dict[str, Any]:
    """
    Update references to compatibility layer in the specified directories.
    
    Args:
        directories: List of directories to update
        dry_run: Whether to perform a dry run (no actual changes)
        
    Returns:
        Summary dictionary with statistics
    """
    summary = {
        "files_checked": 0,
        "files_updated": 0,
        "lines_checked": 0,
        "lines_updated": 0,
        "updates": {}
    }
    
    # Find references
    references = find_compatibility_references(directories)
    
    # Update references
    for file_path, _ in references.items():
        summary["files_checked"] += 1
        
        # Update the file
        lines_checked, lines_updated, updates = update_file(file_path, dry_run)
        
        summary["lines_checked"] += lines_checked
        
        # Track updates
        if lines_updated > 0:
            summary["files_updated"] += 1
            summary["lines_updated"] += lines_updated
            summary["updates"][file_path] = updates
    
    return summary


def main():
    """Run the update imports script."""
    # Parse arguments
    parser = argparse.ArgumentParser(description="Update imports script for Zendesk AI Integration")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no files will be modified)")
    parser.add_argument("--directories", nargs='+', default=["src", "tests"], help="Directories to update")
    args = parser.parse_args()
    
    # Log script start
    logger.info("Starting update imports script")
    if args.dry_run:
        logger.info("Performing dry run (no files will be modified)")
    
    # Update references
    summary = update_compatibility_references(args.directories, args.dry_run)
    
    # Print summary
    print("\nUpdate Summary:")
    print(f"- Files checked: {summary['files_checked']}")
    print(f"- Files updated: {summary['files_updated']}")
    print(f"- Lines checked: {summary['lines_checked']}")
    print(f"- Lines updated: {summary['lines_updated']}")
    
    # Print detailed updates
    if summary['updates']:
        print("\nDetailed Updates:")
        for file_path, updates in summary['updates'].items():
            print(f"\n{file_path}:")
            for line_num, update in updates.items():
                print(f"  Line {line_num}:")
                print(f"    - Old: {update['old']}")
                print(f"    - New: {update['new']}")
    
    # Log script end
    logger.info("Update imports script completed")
    
    # Return success
    return 0


if __name__ == "__main__":
    main()
