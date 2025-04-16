"""
Zendesk AI Integration Modules Package

This package contains the modular components of the Zendesk AI Integration application.
Each module has a single responsibility, following the Single Responsibility Principle:

- zendesk_client.py: Handles all interactions with the Zendesk API
- ai_analyzer.py: Processes ticket content using AI services
- db_repository.py: Handles database operations
- webhook_server.py: Provides a Flask server for handling Zendesk webhooks
- scheduler.py: Manages scheduled tasks
- cli.py: Handles command-line interface and argument parsing
- reporters/: Package containing report generators for different report types
"""
