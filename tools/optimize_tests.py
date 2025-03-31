#!/usr/bin/env python
"""
Test optimization tool for Zendesk AI Integration.

This script identifies slow-running tests and provides suggestions for optimization.
Usage: python tools/optimize_tests.py [--threshold 1.0]
"""

import argparse
import json
import os
import sys
import subprocess
import re
from collections import defaultdict
from datetime import datetime

def run_pytest_with_timing(test_paths=None, verbose=True, output_file=None):
    """Run pytest with the --duration option to get timing information."""
    if test_paths is None:
        test_paths = ["tests"]
    
    cmd = ["pytest", "--durations=0"]
    if verbose:
        cmd.append("-v")
    
    cmd.extend(test_paths)
    
    print(f"Running tests with timing information...")
    print(f"Command: {' '.join(cmd)}")
    
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Tests failed with the following output:")
        print(result.stdout)
        print(result.stderr)
        return None
    
    return result.stdout if not output_file else None

def parse_test_durations(output_file=None, stdout=None):
    """Parse pytest output to extract test durations."""
    if output_file and os.path.exists(output_file):
        with open(output_file, "r") as f:
            content = f.read()
    elif stdout:
        content = stdout
    else:
        print("Error: No test output provided.")
        return None
    
    # Extract timing information section
    timing_section = re.search(r"=+\s+slowest\s+durations\s+=+\n(.*?)(?=\n=+|$)", 
                              content, re.DOTALL)
    
    if not timing_section:
        print("No timing information found in test output.")
        return []
    
    timing_lines = timing_section.group(1).strip().split("\n")
    
    # Parse each line for test name and duration
    durations = []
    for line in timing_lines:
        if not line.strip():
            continue
        
        # Extract time and test name using regex
        match = re.match(r"(\d+\.\d+)s(?: call)?\s+(.*)", line.strip())
        if match:
            duration = float(match.group(1))
            test_name = match.group(2).strip()
            
            # Extract test file, class, and method
            parts = test_name.split("::")
            test_file = parts[0] if len(parts) > 0 else ""
            test_class = parts[1] if len(parts) > 1 else ""
            test_method = parts[2] if len(parts) > 2 else ""
            
            durations.append({
                "duration": duration,
                "test_name": test_name,
                "test_file": test_file,
                "test_class": test_class,
                "test_method": test_method
            })
    
    return durations

def analyze_slow_tests(durations, threshold=1.0):
    """Analyze slow test data and generate optimization suggestions."""
    if not durations:
        return {
            "total_tests": 0,
            "slow_tests": [],
            "file_stats": {},
            "class_stats": {},
            "suggestions": []
        }
    
    # Filter to slow tests above threshold
    slow_tests = [t for t in durations if t["duration"] >= threshold]
    
    # Aggregate stats by file and class
    file_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0, "tests": []})
    class_stats = defaultdict(lambda: {"count": 0, "total_time": 0.0, "tests": []})
    
    for test in durations:
        file_key = test["test_file"]
        class_key = f"{test['test_file']}::{test['test_class']}" if test["test_class"] else file_key
        
        file_stats[file_key]["count"] += 1
        file_stats[file_key]["total_time"] += test["duration"]
        file_stats[file_key]["tests"].append(test)
        
        class_stats[class_key]["count"] += 1
        class_stats[class_key]["total_time"] += test["duration"]
        class_stats[class_key]["tests"].append(test)
    
    # Generate optimization suggestions
    suggestions = []
    
    # 1. Check for test files with high total time
    slow_files = [(file, stats) for file, stats in file_stats.items() 
                 if stats["total_time"] >= threshold * 3]
    if slow_files:
        for file, stats in sorted(slow_files, key=lambda x: x[1]["total_time"], reverse=True):
            suggestions.append({
                "type": "slow_file",
                "message": f"Test file '{file}' has {stats['count']} tests taking {stats['total_time']:.2f}s total",
                "file": file,
                "time": stats["total_time"],
                "recommendation": "Consider splitting this test file or refactoring setup/teardown"
            })
    
    # 2. Check for test classes with high total time
    slow_classes = [(cls, stats) for cls, stats in class_stats.items() 
                   if stats["total_time"] >= threshold * 2 and "::" in cls]
    if slow_classes:
        for cls, stats in sorted(slow_classes, key=lambda x: x[1]["total_time"], reverse=True):
            file, class_name = cls.split("::", 1)
            suggestions.append({
                "type": "slow_class",
                "message": f"Test class '{class_name}' in '{file}' has {stats['count']} tests taking {stats['total_time']:.2f}s total",
                "file": file,
                "class": class_name,
                "time": stats["total_time"],
                "recommendation": "Check class fixtures and improve class setup/teardown efficiency"
            })
    
    # 3. Individual very slow tests (significant outliers)
    extreme_outliers = [t for t in durations if t["duration"] >= threshold * 3]
    if extreme_outliers:
        for test in sorted(extreme_outliers, key=lambda x: x["duration"], reverse=True):
            suggestions.append({
                "type": "extreme_outlier",
                "message": f"Extremely slow test: {test['test_name']} takes {test['duration']:.2f}s",
                "test_name": test["test_name"],
                "time": test["duration"],
                "recommendation": "Priority for optimization - check for network calls, database operations, or sleep/wait statements"
            })
    
    # 4. Tests with redundant setup
    # Look for patterns in test names that might indicate redundant work
    pattern_tests = defaultdict(list)
    for test in durations:
        if not test["test_method"]:
            continue
        
        # Extract the core test name pattern (removing test_ prefix and parameterization)
        core_name = re.sub(r'test_', '', test["test_method"])
        core_name = re.sub(r'\[.*\]$', '', core_name)
        pattern_tests[core_name].append(test)
    
    # Look for similar test methods that might benefit from parameterization
    similar_tests = [(pattern, tests) for pattern, tests in pattern_tests.items() 
                    if len(tests) >= 3 and sum(t["duration"] for t in tests) >= threshold * 2]
    
    if similar_tests:
        for pattern, tests in sorted(similar_tests, key=lambda x: sum(t["duration"] for t in x[1]), reverse=True):
            total_time = sum(t["duration"] for t in tests)
            suggestions.append({
                "type": "similar_tests",
                "message": f"Found {len(tests)} similar tests with pattern '{pattern}' taking {total_time:.2f}s total",
                "pattern": pattern,
                "test_count": len(tests),
                "time": total_time,
                "recommendation": "Consider using parameterized tests to reduce setup/teardown duplication"
            })
    
    # 5. Check if mocks might be missing or inefficient
    potential_mock_issues = []
    for test in slow_tests:
        test_name = test["test_name"].lower()
        # Check for tests that might be doing real API calls or DB operations
        if any(keyword in test_name for keyword in ["api", "service", "client", "db", "database", "mongo", "zendesk"]):
            potential_mock_issues.append(test)
    
    if potential_mock_issues:
        for test in sorted(potential_mock_issues, key=lambda x: x["duration"], reverse=True):
            suggestions.append({
                "type": "mock_issue",
                "message": f"Potentially missing or inefficient mocks: {test['test_name']} takes {test['duration']:.2f}s",
                "test_name": test["test_name"],
                "time": test["duration"],
                "recommendation": "Verify that external services are properly mocked in this test"
            })
    
    return {
        "total_tests": len(durations),
        "slow_tests": slow_tests,
        "file_stats": {file: {**stats, "tests": [t["test_name"] for t in stats["tests"]]} 
                      for file, stats in file_stats.items()},
        "class_stats": {cls: {**stats, "tests": [t["test_name"] for t in stats["tests"]]} 
                       for cls, stats in class_stats.items()},
        "suggestions": suggestions
    }

def generate_optimization_report(analysis, output_file="test_optimization.md"):
    """Generate a markdown report with test optimization suggestions."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = [
        "# Test Optimization Report",
        f"\nGenerated: {now}",
        f"\n## Summary",
        f"- Total tests analyzed: {analysis['total_tests']}",
        f"- Slow tests identified: {len(analysis['slow_tests'])}",
        f"- Optimization suggestions: {len(analysis['suggestions'])}"
    ]
    
    # Top slowest tests
    if analysis['slow_tests']:
        report.append("\n## Top 10 Slowest Tests")
        for test in sorted(analysis['slow_tests'], key=lambda x: x["duration"], reverse=True)[:10]:
            report.append(f"- **{test['test_name']}**: {test['duration']:.2f}s")
    
    # Optimization suggestions by category
    if analysis['suggestions']:
        report.append("\n## Optimization Suggestions")
        
        # Group suggestions by type
        suggestion_by_type = defaultdict(list)
        for suggestion in analysis['suggestions']:
            suggestion_by_type[suggestion['type']].append(suggestion)
        
        # Process extreme outliers first (highest priority)
        if 'extreme_outlier' in suggestion_by_type:
            report.append("\n### Priority Optimizations Needed")
            for suggestion in suggestion_by_type['extreme_outlier']:
                report.append(f"- **{suggestion['test_name']}**: {suggestion['time']:.2f}s")
                report.append(f"  - *Recommendation*: {suggestion['recommendation']}")
        
        # Process slow files
        if 'slow_file' in suggestion_by_type:
            report.append("\n### Test Files to Optimize")
            for suggestion in suggestion_by_type['slow_file']:
                report.append(f"- **{suggestion['file']}**: {suggestion['time']:.2f}s total")
                report.append(f"  - *Recommendation*: {suggestion['recommendation']}")
        
        # Process slow classes
        if 'slow_class' in suggestion_by_type:
            report.append("\n### Test Classes to Optimize")
            for suggestion in suggestion_by_type['slow_class']:
                report.append(f"- **{suggestion['class']}** (in {suggestion['file']}): {suggestion['time']:.2f}s total")
                report.append(f"  - *Recommendation*: {suggestion['recommendation']}")
        
        # Process similar tests that could be parameterized
        if 'similar_tests' in suggestion_by_type:
            report.append("\n### Test Refactoring Opportunities")
            for suggestion in suggestion_by_type['similar_tests']:
                report.append(f"- **Test pattern '{suggestion['pattern']}'**: {suggestion['test_count']} similar tests taking {suggestion['time']:.2f}s")
                report.append(f"  - *Recommendation*: {suggestion['recommendation']}")
        
        # Process mock issues
        if 'mock_issue' in suggestion_by_type:
            report.append("\n### Potential Mocking Issues")
            for suggestion in suggestion_by_type['mock_issue']:
                report.append(f"- **{suggestion['test_name']}**: {suggestion['time']:.2f}s")
                report.append(f"  - *Recommendation*: {suggestion['recommendation']}")
    
    # General optimization strategies
    report.extend([
        "\n## General Optimization Strategies",
        "",
        "### 1. Improve Test Isolation",
        "- Use the right scope for fixtures (function, class, module, session)",
        "- Only set up the components you need for each test",
        "- Avoid test interdependence",
        "",
        "### 2. Mock External Dependencies",
        "- Verify all external APIs and services are properly mocked",
        "- Use in-memory databases for database tests",
        "- Avoid real network calls in unit and integration tests",
        "",
        "### 3. Optimize Setup and Teardown",
        "- Move expensive setup to session or module scope when possible",
        "- Use class fixtures for related tests with similar requirements",
        "- Consider using pytest-xdist for parallel test execution",
        "",
        "### 4. Refactor Test Structure",
        "- Use parameterized tests for similar test cases",
        "- Split large test files into smaller, focused files",
        "- Consider separate test suites for fast vs. slow tests",
        "",
        "### 5. Review Assertions and Logic",
        "- Simplify complex assertions",
        "- Remove unnecessary waits or sleeps",
        "- Use appropriate assertion methods for better performance"
    ])
    
    # Write report to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print(f"Optimization report generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Identify and optimize slow-running tests")
    parser.add_argument("--test-path", nargs="+", default=["tests"],
                        help="Test path(s) to analyze (default: tests)")
    parser.add_argument("--threshold", type=float, default=1.0,
                        help="Threshold in seconds to identify slow tests (default: 1.0)")
    parser.add_argument("--output", default="test_optimization.md",
                        help="Output report file (default: test_optimization.md)")
    parser.add_argument("--raw-output", default="pytest_output.txt",
                        help="Raw pytest output file (default: pytest_output.txt)")
    parser.add_argument("--json", action="store_true",
                        help="Also output analysis as JSON")
    parser.add_argument("--no-run", action="store_true",
                        help="Skip running tests and use existing raw output file")
    args = parser.parse_args()
    
    # Run pytest with timing information
    if not args.no_run:
        stdout = run_pytest_with_timing(args.test_path, output_file=args.raw_output)
    
    # Parse test durations
    durations = parse_test_durations(output_file=args.raw_output)
    if not durations:
        print("No test duration data found. Exiting.")
        sys.exit(1)
    
    # Analyze slow tests
    analysis = analyze_slow_tests(durations, threshold=args.threshold)
    
    # Generate optimization report
    report_file = generate_optimization_report(analysis, output_file=args.output)
    
    # Output JSON if requested
    if args.json:
        json_file = args.output.replace('.md', '.json')
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2)
        print(f"JSON analysis saved to: {json_file}")
    
    # Print summary
    print("\nTEST OPTIMIZATION SUMMARY")
    print(f"Total tests: {analysis['total_tests']}")
    print(f"Slow tests (>{args.threshold}s): {len(analysis['slow_tests'])}")
    print(f"Optimization suggestions: {len(analysis['suggestions'])}")
    
    if analysis['suggestions']:
        print("\nTop 3 suggestions:")
        for suggestion in sorted(analysis['suggestions'], 
                               key=lambda x: 1 if x['type'] == 'extreme_outlier' else 2,
                               reverse=False)[:3]:
            print(f"- {suggestion['message']}")
    
    print(f"\nSee {args.output} for full analysis and optimization guidelines")

if __name__ == "__main__":
    main()
