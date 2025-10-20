"""
Repositories Package

This package contains repositories for data persistence in the Zendesk AI Integration application.
"""

from src.infrastructure.repositories.mongodb_repository import MongoDBRepository
from src.infrastructure.repositories.zendesk_repository import ZendeskRepository

__all__ = ['ZendeskRepository', 'MongoDBRepository']
