"""
MongoDB Repository Implementation

This module provides an implementation of the AnalysisRepository interface
using MongoDB for persistence.
"""

import os
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.domain.entities.ticket_analysis import TicketAnalysis, SentimentAnalysis
from src.domain.interfaces.repository_interfaces import AnalysisRepository
from src.domain.exceptions import ConnectionError, QueryError, PersistenceError

from src.infrastructure.utils.retry import with_retry

# Set up logging
logger = logging.getLogger(__name__)


class MongoDBRepository(AnalysisRepository):
    """
    Implementation of the AnalysisRepository interface using MongoDB.

    This repository uses PyMongo to connect to a MongoDB database and
    store ticket analysis results.
    """

    def __init__(self, mongo_client=None):
        """
        Initialize the MongoDB repository.

        Args:
            mongo_client: Optional pre-configured MongoDB client
        """
        # MongoDB connection details
        self.mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGODB_DB_NAME", "zendesk_analytics")
        self.collection_name = os.getenv("MONGODB_COLLECTION_NAME", "ticket_analysis")

        self.client = mongo_client or self._create_mongo_client()
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

        # Ensure indexes
        self._ensure_indexes()

    def _create_mongo_client(self):
        """
        Create a new MongoDB client using environment variables.

        Returns:
            MongoDB client instance

        Raises:
            ConnectionError: If credentials are missing or invalid
        """
        try:
            # Import pymongo on-demand to avoid making it a domain dependency
            from pymongo import MongoClient

            # Create connection with appropriate timeouts
            client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout for server selection
                connectTimeoutMS=10000,         # 10 second timeout for initial connection
                socketTimeoutMS=45000,          # 45 second timeout for socket operations
                retryWrites=True,               # Enable retryable writes for better reliability
                maxPoolSize=50,                 # Connection pool size
                minPoolSize=10                  # Minimum connections to maintain
            )

            # Ping the server to verify the connection works
            client.admin.command('ping')

            # Don't log the full URI as it may contain credentials
            sanitized_uri = self.mongodb_uri.split('@')[-1] if '@' in self.mongodb_uri else self.mongodb_uri
            logger.info(f"Connected to MongoDB at {sanitized_uri}")

            return client
        except ImportError:
            logger.error("PyMongo package not installed. Install with: pip install pymongo>=4.5.0")
            raise ConnectionError("PyMongo package not installed")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")

    def _ensure_indexes(self):
        """
        Create necessary indexes if they don't exist.

        Raises:
            ConnectionError: If the operation fails
        """
        try:
            # Check if indexes exist, if not create them
            existing_indexes = self.collection.index_information()

            if "ticket_id_1" not in existing_indexes:
                self.collection.create_index([("ticket_id", 1)], background=True)
                logger.info("Created index on 'ticket_id'")

            if "timestamp_1" not in existing_indexes:
                self.collection.create_index([("timestamp", 1)], background=True)
                logger.info("Created index on 'timestamp'")

            if "category_1" not in existing_indexes:
                self.collection.create_index([("category", 1)], background=True)
                logger.info("Created index on 'category'")

            if "sentiment.polarity_1" not in existing_indexes:
                self.collection.create_index([("sentiment.polarity", 1)], background=True)
                logger.info("Created index on 'sentiment.polarity'")

            if "sentiment.business_impact.detected_1" not in existing_indexes:
                self.collection.create_index([("sentiment.business_impact.detected", 1)], background=True)
                logger.info("Created index on 'sentiment.business_impact.detected'")

            # Create recommended indexes
            if "priority_score_1" not in existing_indexes:
                self.collection.create_index([("priority_score", 1)], background=True)
                logger.info("Created index on 'priority_score'")
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            raise ConnectionError(f"Failed to create indexes: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def save(self, analysis: TicketAnalysis) -> str:
        """
        Save a ticket analysis.

        Args:
            analysis: Ticket analysis to save

        Returns:
            ID of the saved analysis

        Raises:
            ConnectionError: If the connection fails
            PersistenceError: If the save operation fails
        """
        # Convert TicketAnalysis entity to a dictionary
        analysis_dict = self._entity_to_dict(analysis)

        try:
            result = self.collection.insert_one(analysis_dict)
            logger.debug(f"Inserted document with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while saving analysis: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error saving analysis to MongoDB: {str(e)}")
                raise PersistenceError(f"Error saving analysis: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def get_by_ticket_id(self, ticket_id: str) -> Optional[TicketAnalysis]:
        """
        Get the most recent analysis for a ticket.

        Args:
            ticket_id: ID of the ticket

        Returns:
            Most recent ticket analysis or None if not found

        Raises:
            ConnectionError: If the connection fails
            QueryError: If the query fails
        """
        try:
            # Sort by timestamp descending to get the most recent analysis
            result = self.collection.find_one(
                {"ticket_id": ticket_id},
                sort=[("timestamp", -1)]
            )

            if result:
                return self._dict_to_entity(result)

            return None
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while fetching analysis: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error fetching analysis from MongoDB: {str(e)}")
                raise QueryError(f"Error fetching analysis: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def find_between_dates(self, start_date: datetime, end_date: datetime) -> List[TicketAnalysis]:
        """
        Find analyses between two dates.

        Args:
            start_date: Start date for the query
            end_date: End date for the query

        Returns:
            List of ticket analyses

        Raises:
            ConnectionError: If the connection fails
            QueryError: If the query fails
        """
        try:
            cursor = self.collection.find({
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            })

            # Convert results to entities
            analyses = [self._dict_to_entity(doc) for doc in cursor]
            logger.info(f"Found {len(analyses)} analyses between {start_date} and {end_date}")

            return analyses
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while finding analyses by date: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error finding analyses by date from MongoDB: {str(e)}")
                raise QueryError(f"Error finding analyses by date: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def find_by_category(self, category: str) -> List[TicketAnalysis]:
        """
        Find analyses by category.

        Args:
            category: Category to search for

        Returns:
            List of ticket analyses

        Raises:
            ConnectionError: If the connection fails
            QueryError: If the query fails
        """
        try:
            cursor = self.collection.find({"category": category})

            # Convert results to entities
            analyses = [self._dict_to_entity(doc) for doc in cursor]
            logger.info(f"Found {len(analyses)} analyses with category '{category}'")

            return analyses
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while finding analyses by category: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error finding analyses by category from MongoDB: {str(e)}")
                raise QueryError(f"Error finding analyses by category: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def find_high_priority(self, min_score: int = 7) -> List[TicketAnalysis]:
        """
        Find high priority analyses.

        Args:
            min_score: Minimum priority score to consider high priority

        Returns:
            List of high priority ticket analyses

        Raises:
            ConnectionError: If the connection fails
            QueryError: If the query fails
        """
        try:
            # In a real system with many documents, we might want to compute
            # and store the priority_score field when saving, but for this
            # implementation, we'll calculate it using the entity's logic

            # First, we need all the documents that might match our criteria
            # This could be inefficient for large collections
            cursor = self.collection.find({
                "$or": [
                    {"priority": "high"},
                    {"priority": "urgent"},
                    {"sentiment.polarity": "negative"},
                    {"sentiment.urgency_level": {"$gte": 4}},
                    {"sentiment.frustration_level": {"$gte": 4}},
                    {"sentiment.business_impact.detected": True}
                ]
            })

            # Convert to entities and filter by priority_score
            all_analyses = [self._dict_to_entity(doc) for doc in cursor]
            high_priority = [a for a in all_analyses if a.priority_score >= min_score]

            logger.info(f"Found {len(high_priority)} high priority analyses (score >= {min_score})")

            return high_priority
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while finding high priority analyses: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error finding high priority analyses from MongoDB: {str(e)}")
                raise QueryError(f"Error finding high priority analyses: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def find_with_business_impact(self) -> List[TicketAnalysis]:
        """
        Find analyses with business impact.

        Returns:
            List of ticket analyses with business impact

        Raises:
            ConnectionError: If the connection fails
            QueryError: If the query fails
        """
        try:
            cursor = self.collection.find({
                "sentiment.business_impact.detected": True
            })

            # Convert results to entities
            analyses = [self._dict_to_entity(doc) for doc in cursor]
            logger.info(f"Found {len(analyses)} analyses with business impact")

            return analyses
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while finding analyses with business impact: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error finding analyses with business impact from MongoDB: {str(e)}")
                raise QueryError(f"Error finding analyses with business impact: {str(e)}")

    @with_retry(max_retries=3, retry_on=Exception)
    def update(self, analysis: TicketAnalysis) -> bool:
        """
        Update an existing analysis.

        Args:
            analysis: Updated ticket analysis

        Returns:
            Success indicator

        Raises:
            ConnectionError: If the connection fails
            PersistenceError: If the update operation fails
        """
        # Convert TicketAnalysis entity to a dictionary
        analysis_dict = self._entity_to_dict(analysis)

        try:
            # Find and update the document with matching ticket_id
            result = self.collection.replace_one(
                {"ticket_id": analysis.ticket_id},
                analysis_dict
            )

            success = result.matched_count > 0

            if success:
                logger.info(f"Updated analysis for ticket {analysis.ticket_id}")
            else:
                logger.warning(f"No matching document found for ticket {analysis.ticket_id}")

            return success
        except Exception as e:
            error_str = str(e).lower()

            if "timeout" in error_str or "connection" in error_str:
                logger.error(f"MongoDB connection error while updating analysis: {str(e)}")
                raise ConnectionError(f"MongoDB connection error: {str(e)}")
            else:
                logger.error(f"Error updating analysis in MongoDB: {str(e)}")
                raise PersistenceError(f"Error updating analysis: {str(e)}")

    def close(self):
        """Close the MongoDB client connection."""
        if self.client:
            self.client.close()
            logger.info("Closed MongoDB connection")

    # Helper methods

    def _entity_to_dict(self, analysis: TicketAnalysis) -> Dict[str, Any]:
        """
        Convert a TicketAnalysis entity to a dictionary for storage.

        Args:
            analysis: TicketAnalysis entity

        Returns:
            Dictionary representation of the entity
        """
        # Start with the sentiment data
        sentiment_dict = {
            "polarity": analysis.sentiment.polarity,
            "urgency_level": analysis.sentiment.urgency_level,
            "frustration_level": analysis.sentiment.frustration_level,
            "emotions": analysis.sentiment.emotions,
            "business_impact": analysis.sentiment.business_impact
        }

        # Build the main dictionary
        analysis_dict = {
            "ticket_id": analysis.ticket_id,
            "subject": analysis.subject,
            "category": analysis.category,
            "component": analysis.component,
            "priority": analysis.priority,
            "sentiment": sentiment_dict,
            "timestamp": analysis.timestamp,
            "confidence": analysis.confidence,
            "priority_score": analysis.priority_score  # Pre-compute for querying
        }

        # Add optional fields if present
        if analysis.source_view_id is not None:
            analysis_dict["source_view_id"] = analysis.source_view_id

        if analysis.source_view_name is not None:
            analysis_dict["source_view_name"] = analysis.source_view_name

        if analysis.raw_result is not None:
            analysis_dict["raw_result"] = analysis.raw_result

        if analysis.error is not None:
            analysis_dict["error"] = analysis.error

        if analysis.error_type is not None:
            analysis_dict["error_type"] = analysis.error_type

        return analysis_dict

    def _dict_to_entity(self, doc: Dict[str, Any]) -> TicketAnalysis:
        """
        Convert a dictionary from MongoDB to a TicketAnalysis entity.

        Args:
            doc: Dictionary from MongoDB

        Returns:
            TicketAnalysis entity
        """
        # Extract sentiment data
        sentiment_data = doc.get("sentiment", {})
        sentiment = SentimentAnalysis(
            polarity=sentiment_data.get("polarity", "unknown"),
            urgency_level=sentiment_data.get("urgency_level", 1),
            frustration_level=sentiment_data.get("frustration_level", 1),
            emotions=sentiment_data.get("emotions", []),
            business_impact=sentiment_data.get("business_impact", {"detected": False})
        )

        # Remove MongoDB's _id field as it's not part of our domain model
        if "_id" in doc:
            doc_copy = doc.copy()
            doc_copy.pop("_id")
        else:
            doc_copy = doc

        # Create the entity
        return TicketAnalysis(
            ticket_id=doc_copy.get("ticket_id", ""),
            subject=doc_copy.get("subject", ""),
            category=doc_copy.get("category", "uncategorized"),
            component=doc_copy.get("component", "none"),
            priority=doc_copy.get("priority", "low"),
            sentiment=sentiment,
            timestamp=doc_copy.get("timestamp", datetime.utcnow()),
            source_view_id=doc_copy.get("source_view_id"),
            source_view_name=doc_copy.get("source_view_name"),
            confidence=doc_copy.get("confidence", 0.0),
            raw_result=doc_copy.get("raw_result"),
            error=doc_copy.get("error"),
            error_type=doc_copy.get("error_type")
        )
