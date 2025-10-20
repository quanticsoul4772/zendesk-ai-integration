"""
Webhook Command

This module defines the WebhookCommand class for managing the webhook server.
"""

import logging
import threading
import time
import signal
import os
import json
from typing import Dict, Any, Optional

from src.presentation.cli.command import Command

# Set up logging
logger = logging.getLogger(__name__)


class WebhookCommand(Command):
    """Command for managing the webhook server."""

    # Class variable to track the webhook server thread
    webhook_thread = None
    is_running = False
    webhook_server = None

    @property
    def name(self) -> str:
        """Get the command name."""
        return "webhook"

    @property
    def description(self) -> str:
        """Get the command description."""
        return "Manage webhook server for real-time ticket analysis"

    def add_arguments(self, parser) -> None:
        """
        Add command-specific arguments to the parser.

        Args:
            parser: ArgumentParser to add arguments to
        """
        subparsers = parser.add_subparsers(dest="subcommand", help="Subcommand")

        # Start webhook subcommand
        start_parser = subparsers.add_parser("start", help="Start the webhook server")
        start_parser.add_argument(
            "--host",
            default="0.0.0.0",
            help="Host to listen on (default: 0.0.0.0)"
        )

        start_parser.add_argument(
            "--port",
            type=int,
            default=5000,
            help="Port to listen on (default: 5000)"
        )

        start_parser.add_argument(
            "--path",
            default="/webhook",
            help="Webhook endpoint path (default: /webhook)"
        )

        start_parser.add_argument(
            "--add-comments",
            action="store_true",
            help="Add analysis as private comments to tickets"
        )

        start_parser.add_argument(
            "--add-tags",
            action="store_true",
            help="Add tags based on analysis to tickets"
        )

        start_parser.add_argument(
            "--log-file",
            help="File to log webhook activity to"
        )

        start_parser.add_argument(
            "--daemon",
            action="store_true",
            help="Run in daemon mode (background)"
        )

        start_parser.add_argument(
            "--pid-file",
            help="File to write PID to when running in daemon mode"
        )

        # Stop webhook subcommand
        stop_parser = subparsers.add_parser("stop", help="Stop the webhook server")
        stop_parser.add_argument(
            "--pid-file",
            help="PID file of the webhook server to stop"
        )

        # Status webhook subcommand
        status_parser = subparsers.add_parser("status", help="Get webhook server status")
        status_parser.add_argument(
            "--pid-file",
            help="PID file of the webhook server to check"
        )

    def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the command.

        Args:
            args: Dictionary of command-line arguments

        Returns:
            Dictionary with execution results
        """
        logger.info(f"Executing webhook command with args: {args}")

        # Determine which subcommand to execute
        subcommand = args.get("subcommand")

        if subcommand == "start":
            return self._start_webhook(args)
        elif subcommand == "stop":
            return self._stop_webhook(args)
        elif subcommand == "status":
            return self._webhook_status(args)
        else:
            # Default to start if no subcommand is specified
            return self._start_webhook(args)

    def _start_webhook(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start the webhook server.

        Args:
            args: Command-line arguments

        Returns:
            Dictionary with execution results
        """
        host = args.get("host", "0.0.0.0")
        port = args.get("port", 5000)
        path = args.get("path", "/webhook")
        add_comments = args.get("add_comments", False)
        add_tags = args.get("add_tags", False)
        log_file = args.get("log_file")
        daemon_mode = args.get("daemon", False)
        pid_file = args.get("pid_file")

        logger.info(f"Starting webhook server on {host}:{port}{path}")

        # Check if already running
        if WebhookCommand.is_running:
            print("Webhook server is already running.")
            return {
                "success": False,
                "error": "Webhook server is already running."
            }

        try:
            # Configure log file if specified
            if log_file:
                webhook_log_handler = logging.FileHandler(log_file)
                webhook_log_handler.setFormatter(
                    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                )
                logging.getLogger().addHandler(webhook_log_handler)
                logger.info(f"Webhook logs will be written to {log_file}")

            # Get webhook service
            webhook_service = self.dependency_container.resolve('webhook_service')

            # Set webhook service preferences
            webhook_service.set_comment_preference(add_comments)
            webhook_service.set_tag_preference(add_tags)

            # Import webhook handler
            from src.presentation.webhook.webhook_handler import WebhookHandler

            # Create webhook handler
            webhook_handler = WebhookHandler(webhook_service)
            WebhookCommand.webhook_server = webhook_handler

            # Run in daemon mode if requested
            if daemon_mode:
                # Fork the process
                pid = os.fork()

                if pid > 0:
                    # Parent process, return success
                    logger.info(f"Started webhook server in daemon mode with PID {pid}")
                    print(f"Started webhook server in daemon mode with PID {pid}")

                    # Write PID to file if specified
                    if pid_file:
                        with open(pid_file, "w") as f:
                            f.write(str(pid))
                        print(f"PID written to {pid_file}")

                    return {
                        "success": True,
                        "host": host,
                        "port": port,
                        "path": path,
                        "daemon": True,
                        "pid": pid,
                        "pid_file": pid_file,
                        "add_comments": add_comments,
                        "add_tags": add_tags
                    }
                else:
                    # Child process, start the server
                    # Detach from parent environment
                    os.setsid()

                    # Set the current working directory
                    os.chdir("/")

                    # Close standard file descriptors
                    os.close(0)
                    os.close(1)
                    os.close(2)

                    # Start the server
                    webhook_handler.start(host, port, path, False)

                    # This code should never be reached
                    os._exit(0)
            else:
                # Run in interactive mode
                # Start webhook server in a separate thread
                WebhookCommand.webhook_thread = threading.Thread(
                    target=webhook_handler.start,
                    args=(host, port, path, False),
                    daemon=True
                )
                WebhookCommand.webhook_thread.start()
                WebhookCommand.is_running = True

                # Print server information
                print(f"Webhook server started on http://{host}:{port}{path}")
                print(f"Configuration:")
                print(f"  - Add comments: {add_comments}")
                print(f"  - Add tags: {add_tags}")
                print("\nPress Ctrl+C to stop the server")

                try:
                    # Keep the main thread running
                    while WebhookCommand.is_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    # Handle Ctrl+C
                    print("\nStopping webhook server...")
                    self._stop_webhook_server()
                    print("Webhook server stopped.")

                    return {
                        "success": True,
                        "message": "Webhook server stopped"
                    }

                return {
                    "success": True,
                    "host": host,
                    "port": port,
                    "path": path,
                    "daemon": False,
                    "add_comments": add_comments,
                    "add_tags": add_tags
                }

        except Exception as e:
            logger.exception(f"Error starting webhook server: {e}")
            print(f"Error starting webhook server: {e}")

            return {
                "success": False,
                "error": str(e)
            }

    def _stop_webhook(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stop the webhook server.

        Args:
            args: Command-line arguments

        Returns:
            Dictionary with execution results
        """
        pid_file = args.get("pid_file")

        if pid_file:
            # Get PID from file
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())

                # Send signal to stop the process
                try:
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(1)  # Give it time to shut down

                    # Check if process still exists
                    try:
                        os.kill(pid, 0)
                        # Process still exists, try SIGKILL
                        os.kill(pid, signal.SIGKILL)
                        print(f"Forcefully terminated webhook server with PID {pid}")
                    except OSError:
                        # Process no longer exists
                        print(f"Webhook server with PID {pid} stopped successfully")

                    # Remove PID file
                    os.remove(pid_file)

                    return {
                        "success": True,
                        "message": f"Webhook server with PID {pid} stopped"
                    }
                except OSError as e:
                    print(f"Error stopping webhook server: {e}")
                    return {
                        "success": False,
                        "error": f"Error stopping webhook server: {str(e)}"
                    }
            except (IOError, ValueError) as e:
                print(f"Error reading PID file: {e}")
                return {
                    "success": False,
                    "error": f"Error reading PID file: {str(e)}"
                }
        else:
            # Stop the webhook server running in the current process
            return self._stop_webhook_server()

    def _stop_webhook_server(self) -> Dict[str, Any]:
        """
        Stop the webhook server running in the current process.

        Returns:
            Dictionary with execution results
        """
        if not WebhookCommand.is_running:
            print("Webhook server is not running.")
            return {
                "success": False,
                "error": "Webhook server is not running."
            }

        # Stop the webhook server
        if WebhookCommand.webhook_server:
            try:
                WebhookCommand.webhook_server.stop()
                WebhookCommand.is_running = False
                WebhookCommand.webhook_server = None
                WebhookCommand.webhook_thread = None

                return {
                    "success": True,
                    "message": "Webhook server stopped"
                }
            except Exception as e:
                logger.exception(f"Error stopping webhook server: {e}")
                print(f"Error stopping webhook server: {e}")

                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            logger.warning("Webhook server not found")
            print("Webhook server not found.")

            return {
                "success": False,
                "error": "Webhook server not found."
            }

    def _webhook_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get webhook server status.

        Args:
            args: Command-line arguments

        Returns:
            Dictionary with execution results
        """
        pid_file = args.get("pid_file")

        if pid_file:
            # Get status from PID file
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())

                # Check if process exists
                try:
                    os.kill(pid, 0)
                    print(f"Webhook server with PID {pid} is running")

                    return {
                        "success": True,
                        "running": True,
                        "pid": pid
                    }
                except OSError:
                    print(f"Webhook server with PID {pid} is not running")

                    return {
                        "success": True,
                        "running": False,
                        "pid": pid
                    }
            except (IOError, ValueError) as e:
                print(f"Error reading PID file: {e}")
                return {
                    "success": False,
                    "error": f"Error reading PID file: {str(e)}"
                }
        else:
            # Get status of webhook server in current process
            if WebhookCommand.is_running:
                print("Webhook server is running.")

                return {
                    "success": True,
                    "running": True
                }
            else:
                print("Webhook server is not running.")

                return {
                    "success": True,
                    "running": False
                }
