"""
Scheduler Service

This module provides the implementation of the SchedulerService interface.
It is responsible for scheduling and managing recurring tasks.
"""

import logging
import time
import threading
import sched
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable

from src.domain.interfaces.service_interfaces import SchedulerService

# Set up logging
logger = logging.getLogger(__name__)


class SchedulerServiceImpl(SchedulerService):
    """
    Implementation of the SchedulerService interface.
    
    This service manages scheduled tasks using Python's sched module
    and provides methods for adding, removing, and listing tasks.
    """
    
    def __init__(self):
        """Initialize the scheduler service."""
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.tasks = {}  # task_name -> task_info
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.RLock()
    
    def schedule_task(self, task_name: str, interval_minutes: int, func: Callable, *args, **kwargs) -> bool:
        """
        Schedule a task to run at regular intervals.
        
        Args:
            task_name: Name of the task
            interval_minutes: Interval in minutes
            func: Function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Success indicator
        """
        with self.lock:
            if task_name in self.tasks:
                logger.warning(f"Task {task_name} is already scheduled. Replacing it.")
                self.remove_task(task_name)
            
            # Convert minutes to seconds
            interval_seconds = interval_minutes * 60
            
            # Create task info
            task_info = {
                'name': task_name,
                'interval_minutes': interval_minutes,
                'interval_seconds': interval_seconds,
                'func': func,
                'args': args,
                'kwargs': kwargs,
                'next_run': time.time(),  # Schedule to run immediately
                'event': None,  # Will be set when scheduled
                'last_run': None,
                'run_count': 0,
                'active': True
            }
            
            # Store the task
            self.tasks[task_name] = task_info
            
            # Schedule the task if the scheduler is running
            if self.running:
                self._schedule_next_run(task_name)
            
            logger.info(f"Scheduled task {task_name} to run every {interval_minutes} minutes")
            return True
    
    def remove_task(self, task_name: str) -> bool:
        """
        Remove a scheduled task.
        
        Args:
            task_name: Name of the task to remove
            
        Returns:
            Success indicator
        """
        with self.lock:
            if task_name not in self.tasks:
                logger.warning(f"Task {task_name} not found")
                return False
            
            # Cancel any pending events
            task_info = self.tasks[task_name]
            if task_info['event'] is not None:
                try:
                    self.scheduler.cancel(task_info['event'])
                except ValueError:
                    # Event might have already been executed
                    pass
            
            # Remove the task
            del self.tasks[task_name]
            
            logger.info(f"Removed task {task_name}")
            return True
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        List all scheduled tasks.
        
        Returns:
            List of task information
        """
        with self.lock:
            task_list = []
            
            for task_name, task_info in self.tasks.items():
                # Create a copy of task info without function objects
                task_copy = task_info.copy()
                task_copy.pop('func')
                task_copy.pop('event')
                
                # Calculate next run time as a human-readable string
                if task_copy['next_run']:
                    next_run_time = datetime.fromtimestamp(task_copy['next_run'])
                    task_copy['next_run_time'] = next_run_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Calculate last run time as a human-readable string
                if task_copy['last_run']:
                    last_run_time = datetime.fromtimestamp(task_copy['last_run'])
                    task_copy['last_run_time'] = last_run_time.strftime('%Y-%m-%d %H:%M:%S')
                
                task_list.append(task_copy)
            
            return task_list
    
    def start(self) -> None:
        """Start the scheduler."""
        with self.lock:
            if self.running:
                logger.warning("Scheduler is already running")
                return
            
            self.running = True
            
            # Schedule all tasks
            for task_name in self.tasks:
                self._schedule_next_run(task_name)
            
            # Start the scheduler in a separate thread
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        with self.lock:
            if not self.running:
                logger.warning("Scheduler is not running")
                return
            
            self.running = False
            
            # Cancel all pending events
            for task_name, task_info in self.tasks.items():
                if task_info['event'] is not None:
                    try:
                        self.scheduler.cancel(task_info['event'])
                    except ValueError:
                        # Event might have already been executed
                        pass
                    task_info['event'] = None
            
            # Clear the scheduler
            for event in self.scheduler.queue:
                try:
                    self.scheduler.cancel(event)
                except ValueError:
                    pass
            
            logger.info("Scheduler stopped")
    
    def _run_scheduler(self) -> None:
        """Run the scheduler in a loop."""
        while self.running:
            try:
                # Run the scheduler
                self.scheduler.run(blocking=False)
                
                # Sleep for a short time
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in scheduler: {str(e)}")
    
    def _schedule_next_run(self, task_name: str) -> None:
        """
        Schedule the next run of a task.
        
        Args:
            task_name: Name of the task to schedule
        """
        if not self.running:
            return
        
        task_info = self.tasks[task_name]
        
        # Check if the task is active
        if not task_info['active']:
            return
        
        # Calculate the delay
        now = time.time()
        delay = max(0, task_info['next_run'] - now)
        
        # Schedule the task
        event = self.scheduler.enter(
            delay, 
            1,  # Priority (1 is highest)
            self._execute_task,
            (task_name,)
        )
        
        # Update task info
        task_info['event'] = event
    
    def _execute_task(self, task_name: str) -> None:
        """
        Execute a task and schedule its next run.
        
        Args:
            task_name: Name of the task to execute
        """
        with self.lock:
            if task_name not in self.tasks:
                return
            
            task_info = self.tasks[task_name]
            
            # Update task info
            task_info['event'] = None
            task_info['last_run'] = time.time()
            task_info['run_count'] += 1
            
            # Calculate next run time
            task_info['next_run'] = time.time() + task_info['interval_seconds']
            
            # Schedule next run
            self._schedule_next_run(task_name)
        
        # Execute the task outside the lock
        try:
            task_info['func'](*task_info['args'], **task_info['kwargs'])
            logger.info(f"Successfully executed task {task_name}")
        except Exception as e:
            logger.error(f"Error executing task {task_name}: {str(e)}")
