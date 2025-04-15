#!/usr/bin/env python
"""
Test Gap Identifier for Zendesk AI Integration.

This script analyzes coverage reports to identify areas needing additional tests,
focusing on high-priority modules with insufficient test coverage.

Usage: python tools/identify_test_gaps.py [--output-file gaps_report.md]
"""

import argparse
import json
import os
import sys
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

# Define risk categories and code patterns that need thorough testing
RISK_CATEGORIES = {
    "high": {
        "modules": [
            "ai_service.py",
            "claude_service.py",
            "enhanced_sentiment.py", 
            "claude_enhanced_sentiment.py",
            "cache_manager.py",
            "batch_processor.py", 
            "db_repository.py"
        ],
        "threshold": 85.0
    },
    "medium": {
        "modules": [
            "zendesk_client.py",
            "cli.py",
            "reporters"
        ],
        "threshold": 75.0
    },
    "low": {
        "modules": [],  # Other modules fall here by default
        "threshold": 60.0
    }
}

# Code patterns requiring thorough testing
CRITICAL_PATTERNS = [
    {
        "name": "Error handling",
        "regex": r"try\s*:.+?except\s+(?:\w+(?:\s*,\s*\w+)*\s*)?:",
        "description": "Error handling code needs thorough testing of both happy and error paths",
        "priority": "high"
    },
    {
        "name": "API calls",
        "regex": r"(?:requests|httpx)\.(?:get|post|put|delete|patch)\s*\(",
        "description": "External API calls need testing with mocks and error scenarios",
        "priority": "high"
    },
    {
        "name": "Database operations",
        "regex": r"(?:collection|db|mongo|cursor)\.(?:find|insert|update|delete|aggregate)\w*\s*\(",
        "description": "Database operations should be tested with various inputs and error cases",
        "priority": "high"
    },
    {
        "name": "File operations",
        "regex": r"(?:open|file)\s*\(.+?,\s*['\"](?:w|r|a|wb|rb|ab)['\"]",
        "description": "File I/O operations need tests for different file states and error handling",
        "priority": "medium"
    },
    {
        "name": "Complex conditionals",
        "regex": r"if\s+.+?(?:and|or).+?(?:and|or).+?:",
        "description": "Complex conditional logic needs tests for all branches",
        "priority": "medium"
    },
    {
        "name": "JSON parsing",
        "regex": r"json\.(?:loads|dumps)\s*\(",
        "description": "JSON parsing should be tested with valid and invalid inputs",
        "priority": "medium"
    },
    {
        "name": "Regular expressions",
        "regex": r"re\.(?:match|search|findall|sub|split)\s*\(",
        "description": "Regular expression usage should have tests for various input patterns",
        "priority": "medium"
    },
    {
        "name": "Authentication",
        "regex": r"(?:auth|token|apikey|password|secret|credential)",
        "description": "Authentication code requires thorough security testing",
        "priority": "high"
    },
    {
        "name": "Parallel processing",
        "regex": r"(?:Thread|ThreadPool|concurrent\.futures|multiprocessing|async|await)",
        "description": "Parallel processing code needs tests for race conditions and thread safety",
        "priority": "high"
    }
]

def get_module_risk_level(module_name):
    """Determine the risk level of a module based on its name."""
    for risk_level, data in RISK_CATEGORIES.items():
        if any(module_name.endswith(mod) or mod in module_name for mod in data["modules"]):
            return risk_level
    return "low"  # Default risk level

def parse_coverage_xml(coverage_file="coverage.xml"):
    """Parse the coverage XML file and extract key metrics."""
    if not os.path.exists(coverage_file):
        print(f"Error: Coverage file {coverage_file} not found.")
        print("Run 'pytest --cov=src --cov-report=xml' to generate it.")
        sys.exit(1)
    
    tree = ET.parse(coverage_file)
    root = tree.getroot()
    
    # Extract module-level metrics
    modules = []
    for package in root.findall(".//package"):
        for module in package.findall("classes/class"):
            module_filename = module.attrib.get("filename", "")
            module_name = module_filename.split("/")[-1]
            
            # Get module coverage
            line_rate = float(module.attrib.get("line-rate", 0)) * 100
            
            # Get uncovered lines
            uncovered_lines = []
            line_nodes = module.findall(".//line")
            for line in line_nodes:
                if line.attrib.get("hits", "0") == "0":
                    uncovered_lines.append(int(line.attrib.get("number", 0)))
            
            # Get risk level
            risk_level = get_module_risk_level(module_name)
            threshold = RISK_CATEGORIES[risk_level]["threshold"]
            
            modules.append({
                "name": module_name,
                "path": module_filename,
                "line_rate": line_rate,
                "uncovered_lines": uncovered_lines,
                "risk_level": risk_level,
                "threshold": threshold,
                "below_threshold": line_rate < threshold
            })
    
    return modules

def analyze_code_patterns(file_path, patterns=CRITICAL_PATTERNS):
    """Analyze source code for critical patterns that need testing."""
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Try with different encoding if utf-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return []
    
    # Find all occurrences of critical patterns
    pattern_matches = []
    for pattern in patterns:
        matches = list(re.finditer(pattern["regex"], content))
        if matches:
            # Get line numbers for each match
            line_numbers = []
            for match in matches:
                # Count newlines up to the match position
                line_num = content[:match.start()].count('\n') + 1
                line_numbers.append(line_num)
            
            pattern_matches.append({
                "pattern_name": pattern["name"],
                "description": pattern["description"],
                "priority": pattern["priority"],
                "match_count": len(matches),
                "line_numbers": line_numbers
            })
    
    return pattern_matches

def identify_test_gaps(modules, src_dir="src"):
    """Identify testing gaps and generate recommendations."""
    gaps = []
    
    # First, check modules below threshold
    below_threshold_modules = [m for m in modules if m["below_threshold"]]
    for module in below_threshold_modules:
        # Full path to the source file
        module_path = os.path.join(src_dir, module["path"])
        
        # Find critical patterns in the code
        patterns = analyze_code_patterns(module_path)
        
        # Calculate the gap to reach threshold
        coverage_gap = module["threshold"] - module["line_rate"]
        
        # Count uncovered critical patterns
        uncovered_critical_patterns = []
        for pattern in patterns:
            # Check if pattern lines overlap with uncovered lines
            overlapping_lines = set(pattern["line_numbers"]).intersection(set(module["uncovered_lines"]))
            if overlapping_lines:
                pattern_copy = pattern.copy()
                pattern_copy["uncovered_lines"] = sorted(list(overlapping_lines))
                uncovered_critical_patterns.append(pattern_copy)
        
        gaps.append({
            "module": module["name"],
            "path": module["path"],
            "risk_level": module["risk_level"],
            "current_coverage": module["line_rate"],
            "threshold": module["threshold"],
            "coverage_gap": coverage_gap,
            "uncovered_lines": len(module["uncovered_lines"]),
            "uncovered_patterns": uncovered_critical_patterns,
            "recommendation": (
                f"Add tests focusing on the {len(uncovered_critical_patterns)} "
                f"uncovered critical patterns to increase coverage by {coverage_gap:.1f}%"
            )
        })
    
    # Also check modules above threshold but with critical patterns uncovered
    for module in [m for m in modules if not m["below_threshold"]]:
        module_path = os.path.join(src_dir, module["path"])
        patterns = analyze_code_patterns(module_path)
        
        # Check if any high priority patterns are uncovered
        uncovered_critical_patterns = []
        for pattern in patterns:
            if pattern["priority"] == "high":
                overlapping_lines = set(pattern["line_numbers"]).intersection(set(module["uncovered_lines"]))
                if overlapping_lines:
                    pattern_copy = pattern.copy()
                    pattern_copy["uncovered_lines"] = sorted(list(overlapping_lines))
                    uncovered_critical_patterns.append(pattern_copy)
        
        if uncovered_critical_patterns:
            gaps.append({
                "module": module["name"],
                "path": module["path"],
                "risk_level": module["risk_level"],
                "current_coverage": module["line_rate"],
                "threshold": module["threshold"],
                "coverage_gap": 0,  # Already above threshold
                "uncovered_lines": len(module["uncovered_lines"]),
                "uncovered_patterns": uncovered_critical_patterns,
                "recommendation": (
                    f"Module meets threshold but has {len(uncovered_critical_patterns)} "
                    f"high priority uncovered patterns that should be tested"
                )
            })
    
    # Sort gaps by risk level and coverage gap
    risk_order = {"high": 0, "medium": 1, "low": 2}
    sorted_gaps = sorted(gaps, key=lambda x: (risk_order[x["risk_level"]], -x["coverage_gap"]))
    
    return sorted_gaps

def generate_gap_report(gaps, output_file="test_gaps_report.md"):
    """Generate a markdown report of testing gaps and recommendations."""
    if not gaps:
        print("No significant testing gaps found!")
        return
    
    report = [
        "# Test Coverage Gap Analysis",
        "\nThis report identifies modules needing additional test coverage, "
        "prioritized by risk level and coverage gap.",
        
        "\n## Summary",
        f"- Total modules with coverage gaps: {len(gaps)}",
        f"- High risk modules: {sum(1 for g in gaps if g['risk_level'] == 'high')}",
        f"- Medium risk modules: {sum(1 for g in gaps if g['risk_level'] == 'medium')}",
        f"- Low risk modules: {sum(1 for g in gaps if g['risk_level'] == 'low')}"
    ]
    
    # Summarize by risk level
    for risk_level in ["high", "medium", "low"]:
        risk_gaps = [g for g in gaps if g["risk_level"] == risk_level]
        if risk_gaps:
            report.append(f"\n## {risk_level.upper()} Risk Modules")
            
            for gap in risk_gaps:
                report.append(f"\n### {gap['module']}")
                report.append(f"- **Current Coverage**: {gap['current_coverage']:.1f}%")
                report.append(f"- **Target Threshold**: {gap['threshold']:.1f}%")
                report.append(f"- **Coverage Gap**: {gap['coverage_gap']:.1f}%")
                report.append(f"- **Uncovered Lines**: {gap['uncovered_lines']}")
                report.append(f"- **Recommendation**: {gap['recommendation']}")
                
                if gap["uncovered_patterns"]:
                    report.append("\n#### Critical Patterns Needing Tests")
                    for pattern in gap["uncovered_patterns"]:
                        report.append(f"- **{pattern['pattern_name']}** (Priority: {pattern['priority']})")
                        report.append(f"  - {pattern['description']}")
                        report.append(f"  - Uncovered at lines: {', '.join(map(str, pattern['uncovered_lines']))}")
    
    # General testing strategies
    report.extend([
        "\n## Testing Strategies",
        "",
        "### Writing Tests for Error Handling",
        "- Use pytest's `pytest.raises` to verify exceptions are thrown correctly",
        "- Mock dependencies to force error conditions",
        "- Test both the exception path and recovery logic",
        "",
        "### Testing External API Calls",
        "- Use mocks to simulate both successful and error responses",
        "- Test timeout scenarios and connection issues",
        "- Verify retry logic if applicable",
        "",
        "### Testing Database Operations",
        "- Use in-memory databases or mocks for test isolation",
        "- Test with various input types and edge cases",
        "- Verify proper handling of database errors",
        "",
        "### Testing Complex Conditionals",
        "- Use parameterized tests to exercise all branches",
        "- Include edge cases and boundary conditions",
        "- Consider using property-based testing for complex inputs"
    ])
    
    # Write report to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print(f"Test gap analysis report generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Identify test coverage gaps")
    parser.add_argument("--coverage-file", default="coverage.xml",
                        help="Path to coverage XML file (default: coverage.xml)")
    parser.add_argument("--src-dir", default="src",
                        help="Source directory (default: src)")
    parser.add_argument("--output-file", default="test_gaps_report.md",
                        help="Output report file (default: test_gaps_report.md)")
    args = parser.parse_args()
    
    # Parse coverage data
    modules = parse_coverage_xml(args.coverage_file)
    
    # Identify testing gaps
    gaps = identify_test_gaps(modules, args.src_dir)
    
    # Generate gap report
    generate_gap_report(gaps, args.output_file)
    
    # Print summary
    print("\nTEST GAP ANALYSIS SUMMARY")
    print(f"Total modules with coverage gaps: {len(gaps)}")
    print(f"High risk modules: {sum(1 for g in gaps if g['risk_level'] == 'high')}")
    print(f"Medium risk modules: {sum(1 for g in gaps if g['risk_level'] == 'medium')}")
    print(f"Low risk modules: {sum(1 for g in gaps if g['risk_level'] == 'low')}")
    
    # Print top gaps to console
    if gaps:
        print("\nTop 3 testing priorities:")
        for gap in gaps[:3]:
            print(f"- {gap['module']} ({gap['risk_level']} risk): {gap['current_coverage']:.1f}% coverage, gap: {gap['coverage_gap']:.1f}%")
    
    print(f"\nSee {args.output_file} for detailed analysis and recommendations")

if __name__ == "__main__":
    main()
