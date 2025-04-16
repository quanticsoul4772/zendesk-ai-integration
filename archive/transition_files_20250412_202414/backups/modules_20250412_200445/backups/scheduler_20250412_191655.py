"""
Scheduler Module

This module handles scheduled tasks for periodic reporting and analysis.
"""

import time
import logging
import schedule
from datetime import datetime, timedelta
import requests
from typing import Dict, Any, Callable

# Set up logging
logger = logging.getLogger(__name__)

class TaskScheduler:
    """
    Manages scheduled tasks for periodic reporting and analysis.
    """
    
    def __init__(self, zendesk_client, ai_analyzer, db_repository):
        """
        Initialize the scheduler.
        
        Args:
            zendesk_client: ZendeskClient instance for ticket operations
            ai_analyzer: AIAnalyzer instance for ticket analysis
            db_repository: DBRepository instance for storing analysis results
        """
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        self.slack_webhook_url = None
        
        # Load Slack webhook URL if available
        self._load_slack_webhook()
    
    def _load_slack_webhook(self):
        """Load Slack webhook URL from environment variables."""
        import os
        from dotenv import load_dotenv
        
        # Load environment variables if not already loaded
        load_dotenv()
        
        # Get Slack webhook URL
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if self.slack_webhook_url and not self.slack_webhook_url.startswith("http"):
            logger.warning("Invalid Slack webhook URL. Notifications will not be sent.")
            self.slack_webhook_url = None
    
    def send_slack_notification(self, message: str) -> bool:
        """
        Send a notification to Slack.
        
        Args:
            message: Message text to send
            
        Returns:
            Boolean indicating success
        """
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured. Notification not sent.")
            return False
        
        try:
            payload = {"text": message}
            response = requests.post(self.slack_webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info("Slack notification sent successfully.")
                return True
            else:
                logger.error(f"Failed to send Slack notification. Status code: {response.status_code}")
                return False
        except Exception as e:
            logger.exception(f"Error sending Slack notification: {e}")
            return False
    
    def daily_summary_task(self):
        """Task for generating daily summary (for test compatibility)."""
        return self.generate_daily_summary()
        
    def generate_daily_summary(self):
        """Generate and send a daily summary of ticket analysis."""
        logger.info("Generating daily summary...")
        
        try:
            # Define cutoff time for daily summary (start of today)
            now = datetime.utcnow()
            cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Query database for recent analyses
            recent_analyses = self.db_repository.find_analyses_since(cutoff)
            total = len(recent_analyses)
            
            # Skip if no analyses found
            if total == 0:
                logger.info("No analyses found for daily summary.")
                return
            
            # Aggregate results
            categories = {}
            components = {}
            sentiments = {}
            
            for record in recent_analyses:
                # Process category
                category = record.get("category", "uncategorized")
                categories[category] = categories.get(category, 0) + 1
                
                # Process component
                component = record.get("component", "none")
                if component != "none":
                    components[component] = components.get(component, 0) + 1
                
                # Process sentiment
                # Handle both basic and enhanced sentiment formats
                sentiment = record.get("sentiment", "unknown")
                if isinstance(sentiment, dict):
                    # Enhanced sentiment
                    polarity = sentiment.get("polarity", "unknown")
                    sentiments[polarity] = sentiments.get(polarity, 0) + 1
                else:
                    # Basic sentiment
                    sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Create summary text
            summary_text = (
                f"Zendesk Daily Summary ({now.strftime('%Y-%m-%d')}):\n"
                f"Tickets Analyzed: {total}\n\n"
                f"Categories:\n" + "\n".join([f"- {k}: {v}" for k, v in categories.items()]) + "\n\n"
            )
            
            if components:
                summary_text += f"Components:\n" + "\n".join([f"- {k}: {v}" for k, v in components.items()]) + "\n\n"
            
            summary_text += f"Sentiments:\n" + "\n".join([f"- {k}: {v}" for k, v in sentiments.items()])
            
            # Log summary
            logger.info(summary_text)
            
            # Send to Slack if configured
            if self.slack_webhook_url:
                self.send_slack_notification(summary_text)
                
        except Exception as e:
            logger.exception(f"Error generating daily summary: {e}")
    
    def weekly_summary_task(self):
        """Task for generating weekly summary (for test compatibility)."""
        return self.generate_weekly_summary()
        
    def generate_weekly_summary(self):
        """Generate and send a weekly summary of ticket analysis."""
        logger.info("Generating weekly summary...")
        
        try:
            # Define cutoff time for weekly summary (7 days ago)
            now = datetime.utcnow()
            cutoff = now - timedelta(days=7)
            
            # Query database for analyses in the past week
            recent_analyses = self.db_repository.find_analyses_since(cutoff)
            total = len(recent_analyses)
            
            # Skip if no analyses found
            if total == 0:
                logger.info("No analyses found for weekly summary.")
                return
            
            # Aggregate results
            categories = {}
            components = {}
            sentiments = {}
            high_priority = 0
            
            for record in recent_analyses:
                # Process category
                category = record.get("category", "uncategorized")
                categories[category] = categories.get(category, 0) + 1
                
                # Process component
                component = record.get("component", "none")
                if component != "none":
                    components[component] = components.get(component, 0) + 1
                
                # Process sentiment
                # Handle both basic and enhanced sentiment formats
                sentiment = record.get("sentiment", "unknown")
                if isinstance(sentiment, dict):
                    # Enhanced sentiment
                    polarity = sentiment.get("polarity", "unknown")
                    sentiments[polarity] = sentiments.get(polarity, 0) + 1
                    
                    # Check for high priority
                    if record.get("priority_score", 0) >= 7:
                        high_priority += 1
                else:
                    # Basic sentiment
                    sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Create summary text
            summary_text = (
                f"Zendesk Weekly Summary ({(now - timedelta(days=7)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}):\n"
                f"Tickets Analyzed: {total}\n"
                f"High Priority Tickets: {high_priority}\n\n"
                f"Categories:\n" + "\n".join([f"- {k}: {v}" for k, v in categories.items()]) + "\n\n"
            )
            
            if components:
                summary_text += f"Components:\n" + "\n".join([f"- {k}: {v}" for k, v in components.items()]) + "\n\n"
            
            summary_text += f"Sentiments:\n" + "\n".join([f"- {k}: {v}" for k, v in sentiments.items()])
            
            # Log summary
            logger.info(summary_text)
            
            # Send to Slack if configured
            if self.slack_webhook_url:
                self.send_slack_notification(summary_text)
                
        except Exception as e:
            logger.exception(f"Error generating weekly summary: {e}")
    
    def add_daily_task(self, task_function, time):
        """
        Add a daily scheduled task.
        
        Args:
            task_function: Function to execute
            time: Time to run task (HH:MM format)
        """
        schedule.every().day.at(time).do(task_function)
        logger.info(f"Scheduled daily task at {time}")
    
    def add_weekly_task(self, task_function, day, time):
        """
        Add a weekly scheduled task.
        
        Args:
            task_function: Function to execute
            day: Day of week to run task
            time: Time to run task (HH:MM format)
        """
        getattr(schedule.every(), day).at(time).do(task_function)
        logger.info(f"Scheduled weekly task on {day} at {time}")
    
    def setup_schedules(self, daily_time="09:00", weekly_day="monday", weekly_time="09:00"):
        """
        Set up scheduled tasks.
        
        Args:
            daily_time: Time to run daily summary (HH:MM format)
            weekly_day: Day of week to run weekly summary
            weekly_time: Time to run weekly summary (HH:MM format)
        """
        # Schedule daily summary using the daily task method
        self.add_daily_task(self.daily_summary_task, daily_time)
        
        # Schedule weekly summary using the weekly task method
        self.add_weekly_task(self.weekly_summary_task, weekly_day, weekly_time)
    
    def run(self):
        """Run the scheduler loop."""
        logger.info("Starting scheduler...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user.")
        except Exception as e:
            logger.exception(f"Error in scheduler loop: {e}")

# For backwards compatibility with tests
Scheduler = TaskScheduler
