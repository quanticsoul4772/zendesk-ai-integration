#!/usr/bin/env python3
"""
A simple script to list Zendesk views directly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def main():
    """Display Zendesk views."""
    try:
        # Import necessary modules
        from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
        
        # Create repository
        zendesk_repo = ZendeskRepository()
        
        # Get all views
        print("Fetching Zendesk views...")
        views = zendesk_repo.get_all_views()
        
        # Sort views by title
        sorted_views = sorted(views, key=lambda v: v.get("title", "").lower())
        
        # Count active and inactive views
        active_views = [v for v in views if v.get("active", True)]
        inactive_views = [v for v in views if not v.get("active", True)]
        
        # Display results
        print(f"\nTotal Views: {len(views)}")
        print(f"Active Views: {len(active_views)}")
        print(f"Inactive Views: {len(inactive_views)}")
        
        print("\nAll Views:")
        print("==========")
        
        for view in sorted_views:
            title = view.get("title", "Unnamed View")
            view_id = view.get("id", "Unknown ID")
            active = "Active" if view.get("active", True) else "Inactive"
            
            print(f"{title} (ID: {view_id}) - {active}")
        
        return 0
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
