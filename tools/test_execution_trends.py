#!/usr/bin/env python
"""
Test Execution Trends for Zendesk AI Integration.

This script tracks test execution times over multiple runs to identify trends
and evaluate the impact of optimization efforts.

Usage: python tools/test_execution_trends.py [--record] [--report]
"""

import argparse
import json
import os
import subprocess
import time
import re
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

# File to store historical test timing data
HISTORY_FILE = "test_execution_history.json"

def run_tests_with_timing(test_paths=None):
    """Run pytest and capture execution time information."""
    if test_paths is None:
        test_paths = ["tests"]
    
    start_time = time.time()
    
    # Run pytest with timing options
    cmd = ["pytest", "--durations=0", "-v"]
    cmd.extend(test_paths)
    
    print(f"Running tests and capturing timing information...")
    print(f"Command: {' '.join(cmd)}")
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Extract test counts from output
    output = process.stdout
    
    # Try to find summary line with test counts
    passed = 0
    failed = 0
    skipped = 0
    total = 0
    
    summary_match = re.search(r"=+ (.*) in [\d\.]+s =+", output.strip().split("\n")[-1])
    if summary_match:
        summary = summary_match.group(1)
        passed_match = re.search(r"(\d+) passed", summary)
        if passed_match:
            passed = int(passed_match.group(1))
        
        failed_match = re.search(r"(\d+) failed", summary)
        if failed_match:
            failed = int(failed_match.group(1))
        
        skipped_match = re.search(r"(\d+) skipped", summary)
        if skipped_match:
            skipped = int(skipped_match.group(1))
        
        total = passed + failed + skipped
    
    # Extract individual test durations
    test_durations = []
    timing_section = re.search(r"=+\s+slowest\s+durations\s+=+\n(.*?)(?=\n=+|$)", 
                              output, re.DOTALL)
    
    if timing_section:
        timing_lines = timing_section.group(1).strip().split("\n")
        
        for line in timing_lines:
            if not line.strip():
                continue
            
            match = re.match(r"(\d+\.\d+)s(?:\s+call)?\s+(.*)", line.strip())
            if match:
                duration = float(match.group(1))
                test_name = match.group(2).strip()
                test_durations.append({
                    "test": test_name,
                    "duration": duration
                })
    
    # Return timing results
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "total_duration": total_duration,
        "tests_total": total,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_skipped": skipped,
        "test_durations": test_durations[:30]  # Only keep top 30 slowest tests
    }

def load_history():
    """Load test execution history from file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading history file: {e}")
        return []

def save_history(history):
    """Save test execution history to file."""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def record_test_run(test_paths=None):
    """Run tests and record timing information."""
    timing_data = run_tests_with_timing(test_paths)
    
    # Load existing history
    history = load_history()
    
    # Add new run data
    history.append(timing_data)
    
    # Save updated history
    save_history(history)
    
    print(f"Recorded test execution (Run #{len(history)})")
    print(f"Total duration: {timing_data['total_duration']:.2f}s")
    print(f"Tests: {timing_data['tests_passed']} passed, {timing_data['tests_failed']} failed, {timing_data['tests_skipped']} skipped")
    
    return timing_data

def generate_trend_report(output_file="test_execution_trends.md"):
    """Generate a markdown report analyzing test execution trends."""
    history = load_history()
    
    if not history or len(history) < 2:
        print("Not enough history data to generate trends (need at least 2 runs)")
        return None
    
    # Extract timing data for analysis
    run_numbers = list(range(1, len(history) + 1))
    total_durations = [run["total_duration"] for run in history]
    
    # Calculate trend indicators
    latest_duration = total_durations[-1]
    previous_duration = total_durations[-2]
    first_duration = total_durations[0]
    
    latest_change = latest_duration - previous_duration
    latest_change_percent = (latest_change / previous_duration) * 100
    
    overall_change = latest_duration - first_duration
    overall_change_percent = (overall_change / first_duration) * 100
    
    # Track test count changes
    latest_count = history[-1]["tests_total"]
    first_count = history[0]["tests_total"]
    test_count_change = latest_count - first_count
    
    # Analyze slow tests across runs
    all_slow_tests = set()
    for run in history:
        for test in run["test_durations"]:
            all_slow_tests.add(test["test"])
    
    # Track each test's duration over time
    test_trends = {test: [] for test in all_slow_tests}
    
    for run in history:
        # Create a lookup for this run
        run_tests = {t["test"]: t["duration"] for t in run["test_durations"]}
        
        # Record duration for each test (or None if not in top 30)
        for test in all_slow_tests:
            test_trends[test].append(run_tests.get(test))
    
    # Identify consistently slow tests (appear in most runs)
    consistent_slow_tests = []
    for test, durations in test_trends.items():
        # Count non-None values
        appearance_count = sum(1 for d in durations if d is not None)
        appearance_rate = appearance_count / len(history)
        
        if appearance_rate >= 0.7:  # In at least 70% of runs
            # Calculate average duration when the test appears
            avg_duration = sum(d for d in durations if d is not None) / appearance_count
            consistent_slow_tests.append({
                "test": test,
                "avg_duration": avg_duration,
                "appearance_rate": appearance_rate
            })
    
    # Sort by average duration
    consistent_slow_tests.sort(key=lambda x: x["avg_duration"], reverse=True)
    
    # Identify improved tests (trending faster)
    improved_tests = []
    for test, durations in test_trends.items():
        # Need at least 2 appearances to calculate trend
        valid_durations = [d for d in durations if d is not None]
        if len(valid_durations) >= 2:
            first_appearance = next((d for d in durations if d is not None), None)
            last_appearance = next((d for d in reversed(durations) if d is not None), None)
            
            if first_appearance and last_appearance:
                change = last_appearance - first_appearance
                change_percent = (change / first_appearance) * 100
                
                if change_percent <= -20:  # At least 20% faster
                    improved_tests.append({
                        "test": test,
                        "first_duration": first_appearance,
                        "last_duration": last_appearance,
                        "change_percent": change_percent
                    })
    
    # Sort by improvement percentage
    improved_tests.sort(key=lambda x: x["change_percent"])
    
    # Generate trend charts
    chart_file = "test_execution_trend_chart.png"
    create_trend_chart(run_numbers, total_durations, chart_file)
    
    # Write the report
    report = [
        "# Test Execution Trend Analysis",
        f"\nReport generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"\n## Summary",
        f"- **Test runs analyzed**: {len(history)}",
        f"- **Latest execution time**: {latest_duration:.2f}s",
        f"- **First execution time**: {first_duration:.2f}s",
        f"- **Overall change**: {overall_change:.2f}s ({overall_change_percent:+.1f}%)",
        f"- **Latest change**: {latest_change:.2f}s ({latest_change_percent:+.1f}%)",
        f"- **Test count change**: {test_count_change:+d} tests since first run",
    ]
    
    # Status indicator based on trends
    if overall_change_percent <= -10:
        report.append(f"- **Status**: 🟢 Significant improvement ({abs(overall_change_percent):.1f}% faster)")
    elif overall_change_percent <= -5:
        report.append(f"- **Status**: 🟡 Moderate improvement ({abs(overall_change_percent):.1f}% faster)")
    elif overall_change_percent >= 10:
        report.append(f"- **Status**: 🔴 Significant slowdown ({overall_change_percent:.1f}% slower)")
    elif overall_change_percent >= 5:
        report.append(f"- **Status**: 🟠 Moderate slowdown ({overall_change_percent:.1f}% slower)")
    else:
        report.append(f"- **Status**: ⚪ Stable (within 5% variation)")
    
    # Add trend visualization
    report.extend([
        "\n## Execution Time Trend",
        f"![Test Execution Trend Chart]({chart_file})"
    ])
    
    # Top consistently slow tests
    if consistent_slow_tests:
        report.append("\n## Consistently Slow Tests")
        report.append("These tests appear in the top 30 slowest tests in most runs:")
        
        for i, test in enumerate(consistent_slow_tests[:10]):  # Top 10
            report.append(f"{i+1}. **{test['test']}**")
            report.append(f"   - Average duration: {test['avg_duration']:.2f}s")
            report.append(f"   - Appears in {test['appearance_rate']*100:.0f}% of test runs")
    
    # Most improved tests
    if improved_tests:
        report.append("\n## Most Improved Tests")
        report.append("These tests have shown the greatest speed improvement:")
        
        for i, test in enumerate(improved_tests[:5]):  # Top 5
            report.append(f"{i+1}. **{test['test']}**")
            report.append(f"   - First recorded: {test['first_duration']:.2f}s")
            report.append(f"   - Latest recorded: {test['last_duration']:.2f}s")
            report.append(f"   - Improvement: {abs(test['change_percent']):.1f}% faster")
    
    # Optimization recommendations
    report.extend([
        "\n## Recommendations",
        "",
        "### Next Optimization Targets",
    ])
    
    if consistent_slow_tests:
        report.append("Focus optimization efforts on these consistently slow tests:")
        for i, test in enumerate(consistent_slow_tests[:3]):
            report.append(f"{i+1}. **{test['test']}** ({test['avg_duration']:.2f}s average)")
    else:
        report.append("No consistently slow tests identified.")
    
    report.extend([
        "",
        "### Optimization Strategies",
        "",
        "1. **Use profiling** on slow tests to identify bottlenecks",
        "2. **Review fixtures** used by slow tests for optimization opportunities",
        "3. **Check for redundant setup** in test classes or modules",
        "4. **Consider parallelization** for independent slow tests",
        "5. **Re-evaluate mocking strategies** for external dependencies"
    ])
    
    # Write report to file
    with open(output_file, "w") as f:
        f.write("\n".join(report))
    
    print(f"Trend report generated: {output_file}")
    return output_file

def create_trend_chart(run_numbers, durations, output_file):
    """Create a chart visualizing test execution time trends."""
    plt.figure(figsize=(10, 6))
    
    # Plot execution time trend
    plt.plot(run_numbers, durations, marker='o', linestyle='-', color='#2C7FB8', linewidth=2)
    
    # Add trendline
    if len(run_numbers) >= 2:
        z = np.polyfit(run_numbers, durations, 1)
        p = np.poly1d(z)
        plt.plot(run_numbers, p(run_numbers), linestyle='--', color='#7F0000', alpha=0.8)
    
    # Add min/max indicators
    min_duration = min(durations)
    min_index = durations.index(min_duration)
    plt.plot(run_numbers[min_index], min_duration, marker='o', color='green', markersize=8)
    
    max_duration = max(durations)
    max_index = durations.index(max_duration)
    plt.plot(run_numbers[max_index], max_duration, marker='o', color='red', markersize=8)
    
    # Annotate latest point
    latest_duration = durations[-1]
    plt.annotate(f"{latest_duration:.2f}s", 
                 (run_numbers[-1], latest_duration),
                 xytext=(5, 10), textcoords='offset points')
    
    # Calculate change percentage
    if len(durations) >= 2:
        first_duration = durations[0]
        change_percent = ((latest_duration - first_duration) / first_duration) * 100
        change_txt = f"{change_percent:+.1f}% since first run"
        
        # Add change annotation
        plt.annotate(change_txt, 
                     (run_numbers[-1], latest_duration),
                     xytext=(5, -20), textcoords='offset points',
                     fontsize=9, color='darkblue')
    
    # Formatting
    plt.title('Test Execution Time Trend')
    plt.xlabel('Run Number')
    plt.ylabel('Execution Time (seconds)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Set x-axis to show only integers
    plt.xticks(run_numbers)
    
    # Save chart
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    
    print(f"Chart saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Track and analyze test execution time trends")
    parser.add_argument("--record", action="store_true",
                        help="Run tests and record timing information")
    parser.add_argument("--report", action="store_true",
                        help="Generate trend report from historical data")
    parser.add_argument("--test-path", nargs="+", default=["tests"],
                        help="Test path(s) to run (for --record)")
    parser.add_argument("--output", default="test_execution_trends.md",
                        help="Output report file (default: test_execution_trends.md)")
    args = parser.parse_args()
    
    # Handle no arguments case (show help)
    if not (args.record or args.report):
        parser.print_help()
        return
    
    # Record new test run if requested
    if args.record:
        record_test_run(args.test_path)
    
    # Generate trend report if requested
    if args.report:
        generate_trend_report(args.output)

if __name__ == "__main__":
    main()
