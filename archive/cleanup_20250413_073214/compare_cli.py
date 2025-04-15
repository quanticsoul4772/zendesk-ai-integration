#!/usr/bin/env python3

"""
CLI Comparison Tool

This script allows running both the legacy and clean architecture CLIs with the same arguments,
making it easier to compare their behavior and ensure feature parity.
"""

import os
import sys
import argparse
import logging
import subprocess
import time
from typing import List, Dict, Any, Tuple
import difflib
import re
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cli_comparison.log')
    ]
)
logger = logging.getLogger(__name__)


def run_legacy_cli(args: List[str]) -> Tuple[str, int]:
    """
    Run the legacy CLI implementation with the given arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Tuple of (output, exit_code)
    """
    logger.info(f"Running legacy CLI with args: {args}")
    
    # Set environment variable to force legacy mode
    env = os.environ.copy()
    env["USE_LEGACY_CLI"] = "1"
    
    # Convert legacy mode arguments
    legacy_args = convert_to_legacy_args(args)
    
    # Build the command
    command = [sys.executable, "run_zendesk_ai.py"] + legacy_args
    
    # Run the command and capture output
    try:
        process = subprocess.run(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Combine stdout and stderr
        output = process.stdout
        if process.stderr.strip():
            output += "\n" + process.stderr
        
        return output, process.returncode
    except Exception as e:
        logger.exception(f"Error running legacy CLI: {e}")
        return f"Error: {e}", 1


def run_clean_cli(args: List[str]) -> Tuple[str, int]:
    """
    Run the clean architecture CLI implementation with the given arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Tuple of (output, exit_code)
    """
    logger.info(f"Running clean CLI with args: {args}")
    
    # Set environment variable to force clean mode
    env = os.environ.copy()
    env["USE_LEGACY_CLI"] = "0"
    
    # Build the command
    command = [sys.executable, "zendesk_cli.py"] + args
    
    # Run the command and capture output
    try:
        process = subprocess.run(
            command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Combine stdout and stderr
        output = process.stdout
        if process.stderr.strip():
            output += "\n" + process.stderr
        
        return output, process.returncode
    except Exception as e:
        logger.exception(f"Error running clean CLI: {e}")
        return f"Error: {e}", 1


def convert_to_legacy_args(args: List[str]) -> List[str]:
    """
    Convert clean architecture arguments to legacy arguments.
    
    Args:
        args: Clean architecture arguments
        
    Returns:
        Legacy arguments
    """
    if not args:
        return []
    
    # Map of clean commands to legacy modes
    command_map = {
        "views": ["--mode", "list-views"],
        "analyze": ["--mode", "run"],
        "report": ["--mode", "report"],
        "interactive": ["--mode", "interactive"],
        "webhook": ["--mode", "webhook"],
        "schedule": ["--mode", "schedule"]
    }
    
    # Map of clean options to legacy options
    option_map = {
        "--view-id": "--view",
        "--view-name": "--view-name",
        "--days": "--days",
        "--limit": "--limit",
        "--format": "--format",
        "--add-comment": "--add-comments",
        "--use-openai": "--use-openai",
        "--output": "--output",
        "--ticket-id": "--ticket-id",
        "--host": "--host",
        "--port": "--port"
    }
    
    # Check if the first argument is a command
    if args[0] in command_map:
        # Replace command with legacy mode
        legacy_args = command_map[args[0]]
        
        # Process the rest of the arguments
        i = 1
        while i < len(args):
            arg = args[i]
            
            # Map options
            if arg in option_map:
                legacy_args.append(option_map[arg])
                
                # Check if next argument is a value
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    legacy_args.append(args[i + 1])
                    i += 2
                else:
                    # Flag option
                    i += 1
            else:
                # Pass through other arguments
                legacy_args.append(arg)
                i += 1
    else:
        # Pass through unknown commands
        legacy_args = args
    
    logger.info(f"Converted {args} to legacy arguments: {legacy_args}")
    return legacy_args


def compare_outputs(legacy_output: str, clean_output: str) -> str:
    """
    Compare the outputs of the legacy and clean CLIs.
    
    Args:
        legacy_output: Output from legacy CLI
        clean_output: Output from clean CLI
        
    Returns:
        Comparison of the outputs
    """
    # Normalize outputs
    legacy_output = normalize_output(legacy_output)
    clean_output = normalize_output(clean_output)
    
    # Generate diff
    diff = difflib.unified_diff(
        legacy_output.splitlines(),
        clean_output.splitlines(),
        fromfile="Legacy CLI",
        tofile="Clean CLI",
        lineterm=""
    )
    
    # Format diff
    formatted_diff = []
    for line in diff:
        if line.startswith("+"):
            formatted_diff.append(f"{Fore.GREEN}{line}{Style.RESET_ALL}")
        elif line.startswith("-"):
            formatted_diff.append(f"{Fore.RED}{line}{Style.RESET_ALL}")
        elif line.startswith("@@"):
            formatted_diff.append(f"{Fore.CYAN}{line}{Style.RESET_ALL}")
        else:
            formatted_diff.append(line)
    
    return "\n".join(formatted_diff)


def normalize_output(output: str) -> str:
    """
    Normalize output for comparison.
    
    Args:
        output: Output to normalize
        
    Returns:
        Normalized output
    """
    # Remove timestamps and other variable parts
    # This is a simplified example, you might need to add more patterns
    patterns = [
        (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}", "TIMESTAMP"),
        (r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "TIMESTAMP"),
        (r"Execution time: \d+\.\d+ seconds", "EXECUTION_TIME"),
        (r"ID: [0-9a-f-]+", "ID: UUID")
    ]
    
    # Apply patterns
    normalized = output
    for pattern, replacement in patterns:
        normalized = re.sub(pattern, replacement, normalized)
    
    return normalized


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Compare legacy and clean architecture CLI implementations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python compare_cli.py views
  python compare_cli.py analyze 12345
  python compare_cli.py report --type sentiment --days 7
  python compare_cli.py interactive
  python compare_cli.py webhook --host 0.0.0.0 --port 5000
"""
    )
    
    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help="Run only the legacy CLI"
    )
    
    parser.add_argument(
        "--clean-only",
        action="store_true",
        help="Run only the clean architecture CLI"
    )
    
    parser.add_argument(
        "--no-compare",
        action="store_true",
        help="Do not compare outputs"
    )
    
    parser.add_argument(
        "--output",
        help="Save output to file"
    )
    
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments to pass to the CLIs"
    )
    
    return parser.parse_args()


def main():
    """Run the CLI comparison tool."""
    # Parse arguments
    args = parse_args()
    
    # Get CLI arguments
    cli_args = args.args
    
    # Run CLIs
    legacy_output = None
    legacy_exit_code = None
    clean_output = None
    clean_exit_code = None
    
    if not args.clean_only:
        print(f"{Fore.YELLOW}Running legacy CLI...{Style.RESET_ALL}")
        start_time = time.time()
        legacy_output, legacy_exit_code = run_legacy_cli(cli_args)
        legacy_time = time.time() - start_time
        print(f"{Fore.YELLOW}Legacy CLI completed in {legacy_time:.2f} seconds with exit code {legacy_exit_code}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Legacy CLI output:{Style.RESET_ALL}")
        print(legacy_output)
    
    if not args.legacy_only:
        print(f"\n{Fore.YELLOW}Running clean architecture CLI...{Style.RESET_ALL}")
        start_time = time.time()
        clean_output, clean_exit_code = run_clean_cli(cli_args)
        clean_time = time.time() - start_time
        print(f"{Fore.YELLOW}Clean architecture CLI completed in {clean_time:.2f} seconds with exit code {clean_exit_code}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Clean architecture CLI output:{Style.RESET_ALL}")
        print(clean_output)
    
    # Compare outputs
    if not args.no_compare and legacy_output is not None and clean_output is not None:
        print(f"\n{Fore.YELLOW}Comparing outputs...{Style.RESET_ALL}")
        comparison = compare_outputs(legacy_output, clean_output)
        print(comparison)
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, legacy_output, clean_output).ratio()
        print(f"\n{Fore.YELLOW}Similarity: {similarity * 100:.2f}%{Style.RESET_ALL}")
        
        # Compare exit codes
        if legacy_exit_code == clean_exit_code:
            print(f"{Fore.GREEN}Exit codes match: {legacy_exit_code}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Exit codes differ: legacy={legacy_exit_code}, clean={clean_exit_code}{Style.RESET_ALL}")
        
        # Compare execution times
        if legacy_time is not None and clean_time is not None:
            time_diff = clean_time - legacy_time
            time_diff_percent = (time_diff / legacy_time) * 100
            
            if time_diff > 0:
                print(f"{Fore.YELLOW}Clean architecture CLI was {time_diff:.2f} seconds ({time_diff_percent:.2f}%) slower{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}Clean architecture CLI was {-time_diff:.2f} seconds ({-time_diff_percent:.2f}%) faster{Style.RESET_ALL}")
    
    # Save output to file
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("=== Legacy CLI Output ===\n")
            if legacy_output is not None:
                f.write(legacy_output)
            f.write("\n\n=== Clean Architecture CLI Output ===\n")
            if clean_output is not None:
                f.write(clean_output)
            f.write("\n\n=== Comparison ===\n")
            if legacy_output is not None and clean_output is not None:
                f.write(comparison)
        
        print(f"\n{Fore.YELLOW}Output saved to {args.output}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
