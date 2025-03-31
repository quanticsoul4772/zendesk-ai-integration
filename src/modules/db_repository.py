"""
Database Repository Module

This module handles all interactions with the MongoDB database.
It provides functions for storing and retrieving analysis data.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables if not already loaded
load_dotenv()

class DBRepository:
    """Handles all database operations for storing and retrieving analysis results."""
    
    def __init__(self):
        """Initialize the database connection."""
        # MongoDB connection details
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGODB_DB_NAME", "zendesk_analytics")
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME", "ticket_analysis")
        self.client = None
        self.db = None
        self.collection = None
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            # Only import MongoDB client when needed
            from pymongo import MongoClient, ASCENDING
            
            # Create connection with appropriate timeouts for cloud connections
            self.client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
                connectTimeoutMS=10000,         # 10 second timeout for initial connection
                socketTimeoutMS=45000,          # 45 second timeout for socket operations
                retryWrites=True,               # Enable retryable writes for better reliability
                maxPoolSize=50,                 # Connection pool size
                minPoolSize=10                  # Minimum connections to maintain
            )
            
            # Ping the server to verify the connection works
            self.client.admin.command('ping')
            
            # Get database and collection
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Ensure we have indexes for faster queries
            self._ensure_indexes()
            
            # Don't log the full URI as it may contain credentials
            sanitized_uri = self.mongodb_uri.split('@')[-1] if '@' in self.mongodb_uri else self.mongodb_uri
            logger.info(f"Connected to MongoDB at {sanitized_uri}")
            
        except ImportError:
            logger.error("PyMongo package not installed. Install with: pip install pymongo>=4.5.0")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _ensure_indexes(self):
        """Create necessary indexes if they don't exist."""
        if self.collection is not None:
            # Check if indexes exist, if not create them
            existing_indexes = self.collection.index_information()
            
            if "ticket_id_1" not in existing_indexes:
                self.collection.create_index([("ticket_id", 1)], background=True)
                logger.info(f"Created index on 'ticket_id'")
            
            if "timestamp_1" not in existing_indexes:
                self.collection.create_index([("timestamp", 1)], background=True)
                logger.info(f"Created index on 'timestamp'")
    
    def save_analysis(self, analysis_data: Dict[str, Any], max_retries: int = 3) -> Optional[str]:
        """
        Save analysis data to MongoDB with retry logic.
        
        Args:
            analysis_data: Analysis data to save
            max_retries: Maximum number of retry attempts
            
        Returns:
            ID of the inserted document or None on failure
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return None
            
        # Ensure timestamp field exists
        if "timestamp" not in analysis_data:
            analysis_data["timestamp"] = datetime.utcnow()
        
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                result = self.collection.insert_one(analysis_data)
                logger.debug(f"Inserted document with ID: {result.inserted_id}")
                return str(result.inserted_id)
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str:
                    logger.warning(f"MongoDB timeout error (attempt {retry_count}/{max_retries}): {e}")
                elif "connection" in error_str:
                    logger.warning(f"MongoDB connection error (attempt {retry_count}/{max_retries}): {e}")
                else:
                    logger.error(f"Error inserting document (attempt {retry_count}/{max_retries}): {e}")
                    
                # Only retry on connection/timeout errors
                if "timeout" not in error_str and "connection" not in error_str:
                    break
                    
                # Wait before retrying (with exponential backoff)
                time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
        
        # If we've exhausted all retries
        logger.error(f"Failed to insert document after {max_retries} attempts")
        return None
    
    def find_analyses_since(self, cutoff_date: datetime, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Find ticket analyses since the given cutoff date.
        
        Args:
            cutoff_date: The cutoff date for the query
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of analysis documents
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return []
            
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                cursor = self.collection.find({"timestamp": {"$gte": cutoff_date}})
                # Immediately convert to list to ensure we've retrieved all data before returning
                return list(cursor)
            except Exception as e:
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str or "connection" in error_str:
                    logger.warning(f"MongoDB query error (attempt {retry_count}/{max_retries}): {e}")
                    
                    # Wait before retrying (with exponential backoff)
                    time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
                else:
                    # Don't retry on non-connection errors
                    logger.error(f"Error querying analyses: {e}")
                    return []
        
        # If we've exhausted all retries
        logger.error(f"Failed to query documents after {max_retries} attempts")
        return []
        
    def find_analyses_between(self, start_date: datetime, end_date: datetime, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Find ticket analyses between two dates.
        
        Args:
            start_date: The start date for the query
            end_date: The end date for the query
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of analysis documents
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return []
            
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                cursor = self.collection.find({
                    "timestamp": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                })
                # Immediately convert to list to ensure we've retrieved all data before returning
                return list(cursor)
            except Exception as e:
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str or "connection" in error_str:
                    logger.warning(f"MongoDB query error (attempt {retry_count}/{max_retries}): {e}")
                    
                    # Wait before retrying (with exponential backoff)
                    time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
                else:
                    # Don't retry on non-connection errors
                    logger.error(f"Error querying analyses: {e}")
                    return []
        
        # If we've exhausted all retries
        logger.error(f"Failed to query documents after {max_retries} attempts")
        return []
        
    def find_high_priority_analyses(self, threshold: int = 7, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Find analyses with high priority scores.
        
        Args:
            threshold: The minimum priority score to consider high priority
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of high priority analysis documents
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return []
            
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                cursor = self.collection.find({"priority_score": {"$gte": threshold}})
                # Immediately convert to list to ensure we've retrieved all data before returning
                return list(cursor)
            except Exception as e:
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str or "connection" in error_str:
                    logger.warning(f"MongoDB query error (attempt {retry_count}/{max_retries}): {e}")
                    
                    # Wait before retrying (with exponential backoff)
                    time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
                else:
                    # Don't retry on non-connection errors
                    logger.error(f"Error querying analyses: {e}")
                    return []
        
        # If we've exhausted all retries
        logger.error(f"Failed to query documents after {max_retries} attempts")
        return []
        
    def find_analyses_with_business_impact(self, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Find analyses where business impact was detected.
        
        Args:
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of analysis documents with business impact
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return []
            
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Query for analyses where business impact was detected
                cursor = self.collection.find({"sentiment.business_impact.detected": True})
                # Immediately convert to list to ensure we've retrieved all data before returning
                return list(cursor)
            except Exception as e:
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str or "connection" in error_str:
                    logger.warning(f"MongoDB query error (attempt {retry_count}/{max_retries}): {e}")
                    
                    # Wait before retrying (with exponential backoff)
                    time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
                else:
                    # Don't retry on non-connection errors
                    logger.error(f"Error querying analyses: {e}")
                    return []
        
        # If we've exhausted all retries
        logger.error(f"Failed to query documents after {max_retries} attempts")
        return []
    
    def get_analysis_by_ticket_id(self, ticket_id: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Find the most recent analysis for a specific ticket.
        
        Args:
            ticket_id: Zendesk ticket ID
            max_retries: Maximum number of retry attempts
            
        Returns:
            The most recent analysis document or None if not found
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return None
            
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Sort by timestamp descending to get the most recent analysis
                result = self.collection.find_one({"ticket_id": ticket_id}, sort=[("timestamp", -1)])
                return result
            except Exception as e:
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str or "connection" in error_str:
                    logger.warning(f"MongoDB query error (attempt {retry_count}/{max_retries}): {e}")
                    
                    # Wait before retrying (with exponential backoff)
                    time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
                else:
                    # Don't retry on non-connection errors
                    logger.error(f"Error getting ticket analysis by ID: {e}")
                    return None
        
        # If we've exhausted all retries
        logger.error(f"Failed to get ticket {ticket_id} analysis after {max_retries} attempts")
        return None
    
    def get_sentiment_statistics(self, time_period: str = "week", max_retries: int = 3) -> Dict[str, Any]:
        """
        Get statistical information about sentiment for a specific time period.
        
        Args:
            time_period: Time period to analyze ('day', 'week', 'month', 'year')
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with sentiment statistics
        """
        # Calculate the start date based on the time period
        from datetime import timedelta
        end_date = datetime.utcnow()
        
        if time_period == "day":
            start_date = end_date - timedelta(days=1)
        elif time_period == "week":
            start_date = end_date - timedelta(days=7)
        elif time_period == "month":
            start_date = end_date - timedelta(days=30)
        elif time_period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)  # Default to week
        
        # Get all analyses in the time period
        analyses = self.find_analyses_between(start_date, end_date)
        
        if not analyses:
            return {
                "count": 0,
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date
            }
        
        # Count sentiment polarities
        polarity_counts = {"positive": 0, "negative": 0, "neutral": 0, "unknown": 0}
        urgency_levels = []
        frustration_levels = []
        priority_scores = []
        business_impact_count = 0
        
        for analysis in analyses:
            # Process sentiment polarity
            sentiment = analysis.get("sentiment", {})
            
            if isinstance(sentiment, dict):
                polarity = sentiment.get("polarity", "unknown")
                polarity_counts[polarity] = polarity_counts.get(polarity, 0) + 1
                
                # Collect metrics for averaging
                urgency = sentiment.get("urgency_level")
                if urgency is not None:
                    urgency_levels.append(urgency)
                    
                frustration = sentiment.get("frustration_level")
                if frustration is not None:
                    frustration_levels.append(frustration)
                    
                # Check for business impact
                business_impact = sentiment.get("business_impact", {})
                if business_impact and business_impact.get("detected", False):
                    business_impact_count += 1
            else:
                # Handle basic sentiment
                polarity = sentiment if isinstance(sentiment, str) else "unknown"
                polarity_counts[polarity] = polarity_counts.get(polarity, 0) + 1
            
            # Process priority score
            priority = analysis.get("priority_score")
            if priority is not None:
                priority_scores.append(priority)
        
        # Calculate averages
        avg_urgency = sum(urgency_levels) / len(urgency_levels) if urgency_levels else 0
        avg_frustration = sum(frustration_levels) / len(frustration_levels) if frustration_levels else 0
        avg_priority = sum(priority_scores) / len(priority_scores) if priority_scores else 0
        
        # Create statistics result
        return {
            "count": len(analyses),
            "time_period": time_period,
            "start_date": start_date,
            "end_date": end_date,
            "sentiment_distribution": polarity_counts,
            "average_urgency": avg_urgency,
            "average_frustration": avg_frustration,
            "average_priority": avg_priority,
            "business_impact_count": business_impact_count,
            "business_impact_percentage": (business_impact_count / len(analyses)) * 100 if analyses else 0
        }
    
    def get_category_distribution(self, time_period: str = "week", max_retries: int = 3) -> Dict[str, int]:
        """
        Get the distribution of ticket categories for a specific time period.
        
        Args:
            time_period: Time period to analyze ('day', 'week', 'month', 'year')
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with category counts
        """
        # Calculate the start date based on the time period
        from datetime import timedelta
        end_date = datetime.utcnow()
        
        if time_period == "day":
            start_date = end_date - timedelta(days=1)
        elif time_period == "week":
            start_date = end_date - timedelta(days=7)
        elif time_period == "month":
            start_date = end_date - timedelta(days=30)
        elif time_period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=7)  # Default to week
        
        # Get all analyses in the time period
        analyses = self.find_analyses_between(start_date, end_date)
        
        if not analyses:
            return {}
        
        # Count categories
        category_counts = {}
        
        for analysis in analyses:
            category = analysis.get("category", "uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return category_counts
    
    def update_analysis(self, analysis_data: Dict[str, Any], max_retries: int = 3) -> Optional[bool]:
        """
        Update an existing analysis document in MongoDB.
        
        Args:
            analysis_data: Updated analysis data
            max_retries: Maximum number of retry attempts
            
        Returns:
            Boolean indicating success or None on failure
        """
        # Check if collection is available
        if self.collection is None:
            logger.error("MongoDB collection is not available")
            return None
            
        # Ensure ticket_id exists for lookup
        if "ticket_id" not in analysis_data:
            logger.error("ticket_id missing from analysis data")
            return None
            
        # Ensure timestamp is updated
        analysis_data["timestamp"] = datetime.utcnow()
        
        # Implement retry pattern for cloud database resilience
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Find and update the document with matching ticket_id
                result = self.collection.replace_one(
                    {"ticket_id": analysis_data["ticket_id"]},
                    analysis_data
                )
                
                if result.matched_count > 0:
                    logger.info(f"Updated analysis for ticket {analysis_data['ticket_id']}")
                    return True
                else:
                    logger.warning(f"No matching document found for ticket {analysis_data['ticket_id']}")
                    return False
                    
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Check for specific Atlas errors
                error_str = str(e).lower()
                if "timeout" in error_str:
                    logger.warning(f"MongoDB timeout error (attempt {retry_count}/{max_retries}): {e}")
                elif "connection" in error_str:
                    logger.warning(f"MongoDB connection error (attempt {retry_count}/{max_retries}): {e}")
                else:
                    logger.error(f"Error updating document (attempt {retry_count}/{max_retries}): {e}")
                    
                # Only retry on connection/timeout errors
                if "timeout" not in error_str and "connection" not in error_str:
                    break
                    
                # Wait before retrying (with exponential backoff)
                time.sleep(2 ** retry_count)  # 2, 4, 8 seconds between retries
        
        # If we've exhausted all retries
        logger.error(f"Failed to update document after {max_retries} attempts")
        return None
        
    def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            self.client = None
            # During pytest teardown, many logging handlers may already be closed
            # Check if logger is still operational before logging
            if logger.handlers and all(hasattr(h, 'stream') and h.stream and not h.stream.closed 
                                      for h in logger.handlers if hasattr(h, 'stream')):
                try:
                    logger.info("Closed MongoDB connection")
                except Exception:
                    # Silently ignore any logging errors during teardown
                    pass
