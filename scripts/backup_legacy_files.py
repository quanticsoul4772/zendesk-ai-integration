#!/usr/bin/env python3
"""
Legacy Component Backup Script

This script creates backups of legacy components before they are removed.
It helps ensure that no functionality is lost during the migration process
and provides a rollback option if needed.

Usage:
    python backup_legacy_files.py [--component component_name]
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
logger = logging.getLogger("backup_script")

# Define legacy components
LEGACY_COMPONENTS = {
    "ai_analyzer": "src/modules/ai_analyzer.py",
    "cache_manager": "src/modules/cache_manager.py",
    "db_repository": "src/modules/db_repository.py",
    "report_generator": "src/modules/report_generator.py",
    "reporters": "src/modules/reporters",
    "scheduler": "src/modules/scheduler.py",
    "webhook_server": "src/modules/webhook_server.py",
    "zendesk_client": "src/modules/zendesk_client.py",
    "service_provider": "src/infrastructure/utils/service_provider.py",
}

def backup_component(root_dir, component_name, backup_dir=None):
    """
    Backup a specific component.
    
    Args:
        root_dir: Root directory of the project
        component_name: Name of the component to backup
        backup_dir: Directory to store backups (default: src/modules/backups)
        
    Returns:
        Path to the backup file or directory
    """
    if component_name not in LEGACY_COMPONENTS:
        logger.error(f"Unknown component: {component_name}")
        return None
    
    source_path = os.path.join(root_dir, LEGACY_COMPONENTS[component_name])
    
    if not os.path.exists(source_path):
        logger.error(f"Component path does not exist: {source_path}")
        return None
    
    # Use default backup directory if not specified
    if not backup_dir:
        backup_dir = os.path.join(root_dir, "src/modules/backups")
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    # Add timestamp to backup name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{component_name}_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Copy the component to the backup location
    try:
        if os.path.isdir(source_path):
            shutil.copytree(source_path, backup_path)
            logger.info(f"Directory {component_name} backed up to {backup_path}")
        else:
            # For files, preserve the extension
            _, ext = os.path.splitext(source_path)
            backup_path += ext
            shutil.copy2(source_path, backup_path)
            logger.info(f"File {component_name} backed up to {backup_path}")
        
        return backup_path
    except Exception as e:
        logger.error(f"Error backing up {component_name}: {e}")
        return None

def backup_all_components(root_dir, backup_dir=None):
    """
    Backup all legacy components.
    
    Args:
        root_dir: Root directory of the project
        backup_dir: Directory to store backups (default: src/modules/backups)
        
    Returns:
        Dictionary mapping component names to backup paths
    """
    results = {}
    
    for component_name in LEGACY_COMPONENTS:
        backup_path = backup_component(root_dir, component_name, backup_dir)
        results[component_name] = backup_path
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Backup legacy components")
    parser.add_argument("--component", help="Name of specific component to backup (default: all)")
    parser.add_argument("--root-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      help="Root directory of the project")
    parser.add_argument("--backup-dir", help="Directory to store backups (default: src/modules/backups)")
    args = parser.parse_args()
    
    if args.component:
        backup_component(args.root_dir, args.component, args.backup_dir)
    else:
        backup_all_components(args.root_dir, args.backup_dir)

if __name__ == "__main__":
    main()
