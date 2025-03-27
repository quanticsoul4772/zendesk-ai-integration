"""
MongoDB Helper module for the Zendesk AI Integration.

This module provides utility functions for working with MongoDB,
including connection management and common query operations.
"""

import os
import logging
import time
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables if not already loaded
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# MongoDB connection details
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "zendesk_analytics")
MONGODB_COLLECTION_NAME = os.getenv("MONGODB_COLLECTION_NAME", "ticket_analysis")

# Global client to reuse connection
_mongo_client = None

def get_mongo_client():
    """
    Get or create MongoDB client with connection pooling optimized for MongoDB Atlas.
    
    Returns:
        A MongoDB client instance.
    """
    global _mongo_client
    
    if _mongo_client is None:
        try:
            # Create connection with appropriate timeouts for cloud connections
            _mongo_client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
                connectTimeoutMS=10000,         # 10 second timeout for initial connection
                socketTimeoutMS=45000,          # 45 second timeout for socket operations
                retryWrites=True,               # Enable retryable writes for better reliability
                maxPoolSize=50,                 # Connection pool size
                minPoolSize=10                  # Minimum connections to maintain
            )
            
            # Ping the server to verify the connection works
            _mongo_client.admin.command('ping')
            
            # Don't log the full URI as it may contain credentials
            sanitized_uri = MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI
            logger.info(f"Connected to MongoDB Atlas at {sanitized_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB Atlas: {e}")
            raise
            
    return _mongo_client

def get_db():
    """
    Get MongoDB database instance.
    
    Returns:
        A MongoDB database instance.
    """
    client = get_mongo_client()
    return client[MONGODB_DB_NAME]

def get_collection(collection_name=None):
    """
    Get MongoDB collection instance.
    
    Args:
        collection_name (str, optional): Name of the collection. Defaults to MONGODB_COLLECTION_NAME.
        
    Returns:
        A MongoDB collection instance.
    """
    db = get_db()
    name = collection_name or MONGODB_COLLECTION_NAME
    
    # Ensure we have an index on ticket_id for faster queries
    collection = db[name]
    
    # Check if index exists, if not create it
    existing_indexes = collection.index_information()
    if "ticket_id_1" not in existing_indexes:
        collection.create_index([("ticket_id", ASCENDING)], background=True)
        logger.info(f"Created index on 'ticket_id' for collection '{name}'")
    
    if "timestamp_1" not in existing_indexes:
        collection.create_index([("timestamp", ASCENDING)], background=True)
        logger.info(f"Created index on 'timestamp' for collection '{name}'")
        
    return collection

def insert_ticket_analysis(ticket_data, max_retries=3):
    """
    Insert ticket analysis data into MongoDB with retry logic for Atlas.
    
    Args:
        ticket_data (dict): Ticket analysis data to insert.
        max_retries (int): Maximum number of retry attempts.
        
    Returns:
        The inserted document ID.
    """
    collection = get_collection()
    
    # Ensure timestamp field exists
    if "timestamp" not in ticket_data:
        ticket_data["timestamp"] = datetime.utcnow()
    
    # Implement retry pattern for cloud database resilience
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            result = collection.insert_one(ticket_data)
            logger.debug(f"Inserted document with ID: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            last_error = e
            retry_count += 1
            
            # Check for specific Atlas errors
            error_str = str(e).lower()
            if "timeout" in error_str:
                logger.warning(f"MongoDB Atlas timeout error (attempt {retry_count}/{max_retries}): {e}")
            elif "connection" in error_str:
                logger.warning(f"MongoDB Atlas connection error (attempt {retry_count}/{max_retries}): {e}")
            else:
                logger.error(f"Error inserting document (attempt {retry_count}/{max_retries}): {e}")
                
            # Only retry on connection/timeout errors
            if "timeout" not in error_str and "connection" not in error_str:
                break
                
            # Wait before retrying (with exponential backoff)
            time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
    
    # If we've exhausted all retries
    logger.error(f"Failed to insert document after {max_retries} attempts")
    raise last_error or Exception("Unknown error during document insertion")

def find_analyses_since(cutoff_date, max_retries=3):
    """
    Find ticket analyses since the given cutoff date with Atlas retry logic.
    
    Args:
        cutoff_date (datetime): The cutoff date for the query.
        max_retries (int): Maximum number of retry attempts.
        
    Returns:
        A list of ticket analysis documents.
    """
    collection = get_collection()
    
    # Implement retry pattern for cloud database resilience
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            cursor = collection.find({"timestamp": {"$gte": cutoff_date}})
            # Immediately convert to list to ensure we've retrieved all data before returning
            return list(cursor)
        except Exception as e:
            retry_count += 1
            
            # Check for specific Atlas errors
            error_str = str(e).lower()
            if "timeout" in error_str or "connection" in error_str:
                logger.warning(f"MongoDB Atlas query error (attempt {retry_count}/{max_retries}): {e}")
                
                # Wait before retrying (with exponential backoff)
                time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
            else:
                # Don't retry on non-connection errors
                logger.error(f"Error querying analyses: {e}")
                return []
    
    # If we've exhausted all retries
    logger.error(f"Failed to query documents after {max_retries} attempts")
    return []

def get_ticket_analysis_by_id(ticket_id, max_retries=3):
    """
    Find the most recent ticket analysis by ticket ID with Atlas retry logic.
    
    Args:
        ticket_id (int): Zendesk ticket ID.
        max_retries (int): Maximum number of retry attempts.
        
    Returns:
        The most recent ticket analysis document for the given ticket, or None if not found.
    """
    collection = get_collection()
    
    # Implement retry pattern for cloud database resilience
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Sort by timestamp descending to get the most recent analysis
            result = collection.find_one({"ticket_id": ticket_id}, sort=[("timestamp", -1)])
            return result
        except Exception as e:
            retry_count += 1
            
            # Check for specific Atlas errors
            error_str = str(e).lower()
            if "timeout" in error_str or "connection" in error_str:
                logger.warning(f"MongoDB Atlas query error (attempt {retry_count}/{max_retries}): {e}")
                
                # Wait before retrying (with exponential backoff)
                time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
            else:
                # Don't retry on non-connection errors
                logger.error(f"Error getting ticket analysis by ID: {e}")
                return None
    
    # If we've exhausted all retries
    logger.error(f"Failed to get ticket {ticket_id} analysis after {max_retries} attempts")
    return None

def close_connections():
    """
    Close MongoDB connections.
    """
    global _mongo_client
    
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None
        logger.info("Closed MongoDB connections")
