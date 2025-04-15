"""
Scheduler Adapter

This module provides an adapter that presents a TaskScheduler interface
but uses the new SchedulerService implementation internally.
"""

import logging
import threading
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta

from src.domain.interfaces.service_interfaces import SchedulerService as SchedulerServiceInterface
from src.application.services.scheduler_service import SchedulerService

# Set up logging
logger = logging.getLogger(__name__)


class SchedulerAdapter:
    """
    Adapter that presents a TaskScheduler interface but uses SchedulerService internally.
    
    This adapter helps with the transition from the legacy TaskScheduler to the
    new SchedulerService implementation.
    """
    
    def __init__(self, scheduler_service=None):
        """
        Initialize the adapter.
        
        Args:
            scheduler_service: Optional SchedulerService instance
        """
        self._scheduler_service = scheduler_service or SchedulerService()
        
        # Legacy compatibility: Store references to services that may be used by legacy code
        self.zendesk_client = None
        self.ai_analyzer = None
        self.db_repository = None
        
        # For backward compatibility, expose the queue attribute
        # that legacy code might expect
        self.queue = []
        
        logger.debug("SchedulerAdapter initialized - using SchedulerService internally")
    
    def set_services(self, zendesk_client, ai_analyzer, db_repository):
        """
        Set the services used by the scheduler (for legacy compatibility).
        
        Args:
            zendesk_client: Zendesk client instance
            ai_analyzer: AI analyzer instance
            db_repository: DB repository instance
        """
        logger.debug("SchedulerAdapter.set_services called")
        
        self.zendesk_client = zendesk_client
        self.ai_analyzer = ai_analyzer
        self.db_repository = db_repository
        
        # Update the scheduler service with repositories if necessary
        if hasattr(self._scheduler_service, 'set_repositories'):
            self._scheduler_service.set_repositories(
                ticket_repository=zendesk_client,
                analysis_repository=db_repository
            )
    
    def add_daily_task(self, task_function, time_str="00:00"):
        """
        Add a task to run daily at a specific time.
        
        Args:
            task_function: Function to run
            time_str: Time to run the task (HH:MM format)
            
        Returns:
            Task ID
        """
        logger.debug(f"SchedulerAdapter.add_daily_task called with time {time_str}")
        
        # Parse the time string
        hour, minute = map(int, time_str.split(':'))
        
        # Add the task using the scheduler service
        task_id = self._scheduler_service.schedule_daily_task(
            task_function,
            hour=hour,
            minute=minute
        )
        
        return task_id
    
    def add_weekly_task(self, task_function, day_of_week="monday", time_str="00:00"):
        """
        Add a task to run weekly on a specific day and time.
        
        Args:
            task_function: Function to run
            day_of_week: Day of the week to run the task
            time_str: Time to run the task (HH:MM format)
            
        Returns:
            Task ID
        """
        logger.debug(f"SchedulerAdapter.add_weekly_task called for {day_of_week} at {time_str}")
        
        # Parse the time string
        hour, minute = map(int, time_str.split(':'))
        
        # Add the task using the scheduler service
        task_id = self._scheduler_service.schedule_weekly_task(
            task_function,
            day_of_week=day_of_week.lower(),
            hour=hour,
            minute=minute
        )
        
        return task_id
    
    def add_interval_task(self, task_function, seconds):
        """
        Add a task to run at a regular interval.
        
        Args:
            task_function: Function to run
            seconds: Interval in seconds
            
        Returns:
            Task ID
        """
        logger.debug(f"SchedulerAdapter.add_interval_task called with interval {seconds} seconds")
        
        # Add the task using the scheduler service
        task_id = self._scheduler_service.schedule_interval_task(
            task_function,
            seconds=seconds
        )
        
        return task_id
    
    def run(self, blocking=True):
        """
        Run the scheduler.
        
        Args:
            blocking: Whether to block the current thread
            
        Returns:
            None
        """
        logger.debug(f"SchedulerAdapter.run called with blocking={blocking}")
        
        if blocking:
            self._scheduler_service.start()
        else:
            # For non-blocking, start in a separate thread
            thread = threading.Thread(target=self._scheduler_service.start)
            thread.daemon = True
            thread.start()
    
    def stop(self):
        """
        Stop the scheduler.
        
        Returns:
            None
        """
        logger.debug("SchedulerAdapter.stop called")
        
        self._scheduler_service.stop()
    
    def cancel(self, task_id):
        """
        Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            Success indicator
        """
        logger.debug(f"SchedulerAdapter.cancel called for task {task_id}")
        
        return self._scheduler_service.cancel_task(task_id)
    
    def enter(self, delay, priority, action, argument=(), kwargs={}):
        """
        Schedule a task to run after a delay.
        
        Args:
            delay: Delay in seconds
            priority: Priority (lower values have higher priority)
            action: Function to run
            argument: Positional arguments tuple
            kwargs: Keyword arguments dictionary
            
        Returns:
            Event object
        """
        logger.debug(f"SchedulerAdapter.enter called with delay {delay}")
        
        # Schedule a one-time task
        task_id = self._scheduler_service.schedule_one_time_task(
            action,
            args=argument,
            kwargs=kwargs,
            delay_seconds=delay
        )
        
        # For backward compatibility, add to queue
        self.queue.append(task_id)
        
        return task_id
    
    def daily_summary_task(self):
        """
        Task to generate a daily summary.
        
        Returns:
            Summary result
        """
        logger.debug("SchedulerAdapter.daily_summary_task called")
        
        # Legacy implementation used services directly
        if not all([self.zendesk_client, self.ai_analyzer, self.db_repository]):
            logger.error("Services not properly initialized for daily_summary_task")
            return None
        
        # Delegate to the scheduler service
        return self._scheduler_service.run_daily_summary()
    
    def weekly_summary_task(self):
        """
        Task to generate a weekly summary.
        
        Returns:
            Summary result
        """
        logger.debug("SchedulerAdapter.weekly_summary_task called")
        
        # Legacy implementation used services directly
        if not all([self.zendesk_client, self.ai_analyzer, self.db_repository]):
            logger.error("Services not properly initialized for weekly_summary_task")
            return None
        
        # Delegate to the scheduler service
        return self._scheduler_service.run_weekly_summary()
