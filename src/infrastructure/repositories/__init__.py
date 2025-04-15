"""
Repositories Package

This package contains repositories for data persistence in the Zendesk AI Integration application.
"""

from src.infrastructure.repositories.zendesk_repository import ZendeskRepository
from src.infrastructure.repositories.mongodb_repository import MongoDBRepository

__all__ = ['ZendeskRepository', 'MongoDBRepository']
