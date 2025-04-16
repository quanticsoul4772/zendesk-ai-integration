"""
Schedule Command

This module defines the ScheduleCommand class for managing scheduled tasks.
"""

import logging
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.presentation.cli.command import Command

# Set up logging
logger = logging.getLogger(__name__)


class ScheduleCommand(Command):
    """Command for managing scheduled tasks."""
    
    @property
    def name(self) -> str:
        """Get the command name."""
        return "schedule"
    
    @property
    def description(self) -> str:
        """Get the command description."""
        return "Set up and manage scheduled analysis jobs"
    
    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.
        
        Args:
            parser: ArgumentParser to add arguments to
        """
        # Create subparsers for each subcommand
        subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand")
        
        # Add subcommand
        add_parser = subparsers.add_parser("add", help="Add a new scheduled task")
        
        # Schedule type group
        schedule_type_group = add_parser.add_mutually_exclusive_group(required=True)
        schedule_type_group.add_argument("--daily", action="store_true", help="Schedule daily task")
        schedule_type_group.add_argument("--weekly", action="store_true", help="Schedule weekly task")
        
        # Time options
        add_parser.add_argument("--daily-time", help="Time to run daily analysis (format: HH:MM)")
        add_parser.add_argument("--weekly-day", type=int, choices=range(0, 7), 
                              help="Day of week to run weekly analysis (0=Monday, 6=Sunday)")
        add_parser.add_argument("--weekly-time", help="Time to run weekly analysis (format: HH:MM)")
        
        # Task options
        add_parser.add_argument("--task", required=True, choices=[
            "daily-summary", "weekly-summary", "analyze-all", "update-views", "sentiment-report", 
            "hardware-report", "pending-report"
        ], help="Task to schedule")
        
        # Task parameters
        add_parser.add_argument("--view-id", type=int, help="View ID to include in scheduled analysis")
        add_parser.add_argument("--view-name", help="View name to include in scheduled analysis")
        add_parser.add_argument("--output-dir", help="Directory to store scheduled reports")
        add_parser.add_argument("--notify", action="store_true", help="Send notification when scheduled reports are complete")
        add_parser.add_argument("--format", choices=["text", "html", "json", "csv"], default="text", 
                              help="Output format for reports")
        add_parser.add_argument("--parameters", help="Additional JSON-formatted parameters for the task")
        
        # List subcommand
        list_parser = subparsers.add_parser("list", help="List scheduled tasks")
        list_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
        list_parser.add_argument("--output", help="Output file path")
        
        # Remove subcommand
        remove_parser = subparsers.add_parser("remove", help="Remove a scheduled task")
        remove_parser.add_argument("--task-id", required=True, help="ID of the task to remove")
        
        # Enable subcommand
        enable_parser = subparsers.add_parser("enable", help="Enable a scheduled task")
        enable_parser.add_argument("--task-id", required=True, help="ID of the task to enable")
        
        # Disable subcommand
        disable_parser = subparsers.add_parser("disable", help="Disable a scheduled task")
        disable_parser.add_argument("--task-id", required=True, help="ID of the task to disable")
        
        # Start subcommand
        start_parser = subparsers.add_parser("start", help="Start the scheduler daemon")
        start_parser.add_argument("--log-file", help="File to log scheduler activity to")
        start_parser.add_argument("--daemon", action="store_true", help="Run in daemon mode (background)")
        start_parser.add_argument("--pid-file", help="File to write PID to when running in daemon mode")
        
        # Stop subcommand
        stop_parser = subparsers.add_parser("stop", help="Stop the scheduler daemon")
        stop_parser.add_argument("--pid-file", help="PID file of the scheduler daemon to stop")
        
        # Run subcommand
        run_parser = subparsers.add_parser("run", help="Run a scheduled task immediately")
        run_parser.add_argument("--task-id", required=True, help="ID of the task to run")
    
    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.
        
        Args:
            args: Dictionary of command-line arguments
            
        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing schedule command with args: {args}")
        
        # Get required services
        scheduler_service = self.dependency_container.resolve('scheduler_service')
        
        # Determine which subcommand to execute
        subcommand = args.get("subcommand")
        
        try:
            if subcommand == "add":
                return self._add_task(args, scheduler_service)
            elif subcommand == "list":
                return self._list_tasks(args, scheduler_service)
            elif subcommand == "remove":
                return self._remove_task(args, scheduler_service)
            elif subcommand == "enable":
                return self._enable_task(args, scheduler_service)
            elif subcommand == "disable":
                return self._disable_task(args, scheduler_service)
            elif subcommand == "start":
                return self._start_scheduler(args, scheduler_service)
            elif subcommand == "stop":
                return self._stop_scheduler(args, scheduler_service)
            elif subcommand == "run":
                return self._run_task(args, scheduler_service)
            else:
                # If no subcommand is specified, show help
                print("Error: No subcommand specified.")
                print("Use 'schedule add', 'schedule list', 'schedule remove', etc.")
                return {
                    "success": False,
                    "error": "No subcommand specified."
                }
        except Exception as e:
            logger.exception(f"Error executing schedule {subcommand} command: {e}")
            print(f"Error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _add_task(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Add a new scheduled task.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        # Determine task type
        task_name = args.get("task")
        
        # Determine schedule type
        is_daily = args.get("daily", False)
        
        # Get schedule parameters
        if is_daily:
            # Get daily time
            daily_time = args.get("daily_time")
            
            if not daily_time:
                raise ValueError("Daily time (--daily-time) must be specified for daily tasks")
            
            # Parse time
            try:
                hour, minute = map(int, daily_time.split(":"))
            except (ValueError, TypeError):
                raise ValueError("Daily time must be in the format HH:MM")
            
            # Schedule daily task
            schedule_type = "daily"
            schedule_time = f"{hour:02d}:{minute:02d}"
            schedule_day = None
            
            logger.info(f"Scheduling daily task {task_name} at {schedule_time}")
        else:
            # Get weekly day and time
            weekly_day = args.get("weekly_day")
            weekly_time = args.get("weekly_time")
            
            if weekly_day is None:
                raise ValueError("Weekly day (--weekly-day) must be specified for weekly tasks")
            
            if not weekly_time:
                raise ValueError("Weekly time (--weekly-time) must be specified for weekly tasks")
            
            # Parse time
            try:
                hour, minute = map(int, weekly_time.split(":"))
            except (ValueError, TypeError):
                raise ValueError("Weekly time must be in the format HH:MM")
            
            # Map day number to day name
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            schedule_day = day_names[weekly_day]
            
            # Schedule weekly task
            schedule_type = "weekly"
            schedule_time = f"{hour:02d}:{minute:02d}"
            
            logger.info(f"Scheduling weekly task {task_name} on {schedule_day} at {schedule_time}")
        
        # Get task parameters
        view_id = args.get("view_id")
        view_name = args.get("view_name")
        output_dir = args.get("output_dir")
        notify = args.get("notify", False)
        format_type = args.get("format", "text")
        
        # Parse additional parameters if provided
        additional_params = {}
        if args.get("parameters"):
            try:
                additional_params = json.loads(args.get("parameters"))
            except json.JSONDecodeError:
                raise ValueError("Parameters must be a valid JSON string")
        
        # Combine all parameters
        task_params = {
            "view_id": view_id,
            "view_name": view_name,
            "output_dir": output_dir,
            "notify": notify,
            "format": format_type,
            **additional_params
        }
        
        # Schedule the task
        if is_daily:
            task_id = scheduler_service.schedule_daily_task(
                task_name=task_name,
                hour=hour,
                minute=minute,
                parameters=task_params
            )
        else:
            task_id = scheduler_service.schedule_weekly_task(
                task_name=task_name,
                day=schedule_day.lower(),
                hour=hour,
                minute=minute,
                parameters=task_params
            )
        
        # Print success message
        if is_daily:
            print(f"Daily task '{task_name}' scheduled at {schedule_time}.")
        else:
            print(f"Weekly task '{task_name}' scheduled on {schedule_day} at {schedule_time}.")
        
        print(f"Task ID: {task_id}")
        
        return {
            "success": True,
            "task_id": task_id,
            "task_name": task_name,
            "schedule_type": schedule_type,
            "schedule_time": schedule_time,
            "schedule_day": schedule_day,
            "parameters": task_params
        }
    
    def _list_tasks(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        List scheduled tasks.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        format_type = args.get("format", "text")
        output_file = args.get("output")
        
        logger.info("Listing scheduled tasks")
        
        # Get all tasks
        tasks = scheduler_service.list_tasks()
        
        # Format the output
        if format_type == "json":
            # JSON format
            output = json.dumps(tasks, indent=2, default=str)
        else:
            # Text format
            if not tasks:
                output = "No scheduled tasks found."
            else:
                output = f"Scheduled Tasks ({len(tasks)}):\n"
                output += "="*40 + "\n\n"
                
                for task in tasks:
                    # Get task details
                    task_id = task.get("id", "Unknown")
                    task_name = task.get("task", "Unknown")
                    schedule = task.get("schedule", "Unknown")
                    next_run = task.get("next_run", "Unknown")
                    enabled = task.get("enabled", True)
                    parameters = task.get("parameters", {})
                    
                    # Format task details
                    output += f"ID: {task_id}\n"
                    output += f"Task: {task_name}\n"
                    output += f"Schedule: {schedule}\n"
                    output += f"Next Run: {next_run}\n"
                    output += f"Status: {'Enabled' if enabled else 'Disabled'}\n"
                    
                    # Add parameters if available
                    if parameters:
                        output += "Parameters:\n"
                        for key, value in parameters.items():
                            if value is not None:
                                output += f"  - {key}: {value}\n"
                    
                    output += "\n"
        
        # Output to file or console
        if output_file:
            # Save to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(output)
            
            print(f"Task list saved to: {os.path.abspath(output_file)}")
        else:
            # Print to console
            print(output)
        
        return {
            "success": True,
            "tasks_count": len(tasks),
            "tasks": tasks
        }
    
    def _remove_task(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Remove a scheduled task.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        task_id = args.get("task_id")
        
        logger.info(f"Removing task {task_id}")
        
        # Remove the task
        success = scheduler_service.remove_task(task_id)
        
        if success:
            print(f"Task {task_id} removed successfully.")
        else:
            print(f"Task {task_id} not found.")
        
        return {
            "success": success,
            "task_id": task_id
        }
    
    def _enable_task(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Enable a scheduled task.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        task_id = args.get("task_id")
        
        logger.info(f"Enabling task {task_id}")
        
        # Enable the task
        success = scheduler_service.enable_task(task_id)
        
        if success:
            print(f"Task {task_id} enabled successfully.")
        else:
            print(f"Task {task_id} not found.")
        
        return {
            "success": success,
            "task_id": task_id
        }
    
    def _disable_task(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Disable a scheduled task.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        task_id = args.get("task_id")
        
        logger.info(f"Disabling task {task_id}")
        
        # Disable the task
        success = scheduler_service.disable_task(task_id)
        
        if success:
            print(f"Task {task_id} disabled successfully.")
        else:
            print(f"Task {task_id} not found.")
        
        return {
            "success": success,
            "task_id": task_id
        }
    
    def _start_scheduler(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Start the scheduler daemon.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        log_file = args.get("log_file")
        daemon_mode = args.get("daemon", False)
        pid_file = args.get("pid_file")
        
        logger.info("Starting scheduler daemon")
        
        # Configure log file if specified
        if log_file:
            scheduler_log_handler = logging.FileHandler(log_file)
            scheduler_log_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logging.getLogger().addHandler(scheduler_log_handler)
            logger.info(f"Scheduler logs will be written to {log_file}")
        
        # Start the scheduler
        if daemon_mode:
            # Run in daemon mode
            pid = scheduler_service.start_daemon(pid_file)
            
            print(f"Scheduler daemon started with PID {pid}")
            if pid_file:
                print(f"PID written to {pid_file}")
            
            return {
                "success": True,
                "daemon": True,
                "pid": pid,
                "pid_file": pid_file
            }
        else:
            # Run in interactive mode
            print("Starting scheduler in interactive mode...")
            print("Press Ctrl+C to stop")
            
            try:
                scheduler_service.start()
            except KeyboardInterrupt:
                print("\nStopping scheduler...")
                scheduler_service.stop()
                print("Scheduler stopped.")
            
            return {
                "success": True,
                "daemon": False
            }
    
    def _stop_scheduler(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Stop the scheduler daemon.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        pid_file = args.get("pid_file")
        
        logger.info("Stopping scheduler daemon")
        
        if pid_file:
            # Stop daemon using PID file
            success = scheduler_service.stop_daemon(pid_file)
            
            if success:
                print("Scheduler daemon stopped successfully.")
            else:
                print("Failed to stop scheduler daemon.")
            
            return {
                "success": success,
                "pid_file": pid_file
            }
        else:
            # Stop local scheduler
            scheduler_service.stop()
            print("Scheduler stopped.")
            
            return {
                "success": True
            }
    
    def _run_task(self, args: Dict[str, Any], scheduler_service) -> Dict[str, Any]:
        """
        Run a scheduled task immediately.
        
        Args:
            args: Command-line arguments
            scheduler_service: Scheduler service
            
        Returns:
            Dictionary with execution results
        """
        task_id = args.get("task_id")
        
        logger.info(f"Running task {task_id} immediately")
        
        # Run the task
        try:
            result = scheduler_service.run_task(task_id)
            
            print(f"Task {task_id} executed successfully.")
            
            # Print result details if available
            if isinstance(result, dict) and "output" in result:
                print(f"Output: {result['output']}")
            
            return {
                "success": True,
                "task_id": task_id,
                "result": result
            }
        except Exception as e:
            print(f"Error executing task {task_id}: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "error": str(e)
            }
