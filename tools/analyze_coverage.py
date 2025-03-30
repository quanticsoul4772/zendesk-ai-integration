#!/usr/bin/env python
"""
Coverage analysis tool for Zendesk AI Integration.

This script analyzes coverage reports to identify gaps and generate actionable insights.
Usage: python tools/analyze_coverage.py [--html-output report.html]
"""

import argparse
import json
import os
import sys
from collections import defaultdict
import xml.etree.ElementTree as ET

# Define risk categories and their coverage thresholds
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
            # All reporter modules should be included
            "reporters",
        ],
        "threshold": 75.0
    },
    "low": {
        "modules": [
            # All other modules fall into this category
        ],
        "threshold": 60.0
    }
}

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
    
    # Extract project-level metrics
    project_metrics = {
        "line_rate": float(root.attrib.get("line-rate", 0)) * 100,
        "branch_rate": float(root.attrib.get("branch-rate", 0)) * 100,
        "complexity": float(root.attrib.get("complexity", 0)),
    }
    
    # Extract module-level metrics
    modules = []
    for package in root.findall(".//package"):
        package_name = package.attrib.get("name", "")
        for module in package.findall("classes/class"):
            module_name = module.attrib.get("filename", "").split("/")[-1]
            line_rate = float(module.attrib.get("line-rate", 0)) * 100
            branch_rate = float(module.attrib.get("branch-rate", 0)) * 100
            
            # Count lines missing coverage
            missing_lines = []
            for line in module.findall(".//line"):
                if line.attrib.get("hits", "0") == "0":
                    missing_lines.append(int(line.attrib.get("number", 0)))
            
            # Get module risk level
            risk_level = get_module_risk_level(module_name)
            threshold = RISK_CATEGORIES[risk_level]["threshold"]
            
            modules.append({
                "name": module_name,
                "path": module.attrib.get("filename", ""),
                "line_rate": line_rate,
                "branch_rate": branch_rate,
                "missing_lines": missing_lines,
                "risk_level": risk_level,
                "threshold": threshold,
                "below_threshold": line_rate < threshold
            })
    
    return {
        "project": project_metrics,
        "modules": modules
    }

def generate_text_report(coverage_data):
    """Generate a text-based coverage report with insights."""
    report = []
    project = coverage_data["project"]
    modules = coverage_data["modules"]
    
    # Overall project stats
    report.append("# Coverage Analysis Report")
    report.append("\n## Project Summary")
    report.append(f"- Overall line coverage: {project['line_rate']:.2f}%")
    report.append(f"- Overall branch coverage: {project['branch_rate']:.2f}%")
    report.append(f"- Code complexity: {project['complexity']:.2f}")
    
    # Count modules below threshold by risk level
    risk_stats = defaultdict(lambda: {"count": 0, "below": 0})
    for module in modules:
        risk_level = module["risk_level"]
        risk_stats[risk_level]["count"] += 1
        if module["below_threshold"]:
            risk_stats[risk_level]["below"] += 1
    
    report.append("\n## Risk Level Summary")
    for risk_level, stats in risk_stats.items():
        threshold = RISK_CATEGORIES[risk_level]["threshold"]
        if stats["count"] > 0:
            below_percent = (stats["below"] / stats["count"]) * 100
            report.append(f"- {risk_level.upper()} risk modules: {stats['below']}/{stats['count']} " 
                         f"({below_percent:.1f}%) below {threshold}% threshold")
    
    # Modules below threshold (prioritized by risk)
    report.append("\n## Modules Below Threshold")
    for risk_level in ["high", "medium", "low"]:
        below_threshold = [m for m in modules if m["risk_level"] == risk_level and m["below_threshold"]]
        if below_threshold:
            report.append(f"\n### {risk_level.upper()} Risk Modules")
            for module in sorted(below_threshold, key=lambda x: x["line_rate"]):
                gap = module["threshold"] - module["line_rate"]
                report.append(f"- {module['name']}: {module['line_rate']:.2f}% " 
                             f"(gap: {gap:.2f}%, needs {len(module['missing_lines'])} more lines covered)")
    
    # Top 10 most uncovered modules (regardless of threshold)
    report.append("\n## Top 10 Modules Needing Coverage Improvement")
    sorted_by_coverage = sorted(modules, key=lambda x: (x["line_rate"], -len(x["missing_lines"])))
    for module in sorted_by_coverage[:10]:
        report.append(f"- {module['name']} ({module['risk_level']} risk): {module['line_rate']:.2f}% covered, "
                     f"{len(module['missing_lines'])} uncovered lines")
    
    # Actionable insights
    report.append("\n## Actionable Insights")
    
    # High risk modules with low coverage
    high_risk_low_cov = [m for m in modules if m["risk_level"] == "high" and m["line_rate"] < 80]
    if high_risk_low_cov:
        report.append("\n### Critical Gaps")
        report.append("These high-risk modules need immediate attention:")
        for module in high_risk_low_cov:
            report.append(f"- {module['name']}: {module['line_rate']:.2f}% (target: {module['threshold']}%)")
    
    # Complex modules with coverage gaps
    # This would require complexity metrics per module, but we'll simplify
    report.append("\n### Suggested Next Steps")
    report.append("1. Focus first on high-risk modules below threshold")
    report.append("2. Then address medium-risk modules with the largest coverage gaps")
    report.append("3. Review modules with many uncovered lines, even if percentage is acceptable")
    report.append("4. Consider adding more edge case and error handling tests")
    
    return "\n".join(report)

def generate_html_report(coverage_data, output_file="coverage_analysis.html"):
    """Generate an HTML coverage report with visualizations."""
    # Simple HTML report generation
    # In a real implementation, you might use a template engine or include charts
    html = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "    <title>Coverage Analysis Report</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 20px; }",
        "        .high { color: #721c24; background-color: #f8d7da; }",
        "        .medium { color: #856404; background-color: #fff3cd; }",
        "        .low { color: #0c5460; background-color: #d1ecf1; }",
        "        .below-threshold { font-weight: bold; }",
        "        table { border-collapse: collapse; width: 100%; }",
        "        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
        "        th { background-color: #f2f2f2; }",
        "        .progress-bar-container { width: 100px; background-color: #e0e0e0; }",
        "        .progress-bar { height: 20px; background-color: #4CAF50; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <h1>Coverage Analysis Report</h1>",
        
        "    <h2>Project Summary</h2>",
        "    <p>",
        f"        Overall line coverage: {coverage_data['project']['line_rate']:.2f}%<br>",
        f"        Overall branch coverage: {coverage_data['project']['branch_rate']:.2f}%<br>",
        f"        Code complexity: {coverage_data['project']['complexity']:.2f}",
        "    </p>",
        
        "    <h2>Modules Coverage</h2>",
        "    <table>",
        "        <tr>",
        "            <th>Module</th>",
        "            <th>Risk Level</th>",
        "            <th>Line Coverage</th>",
        "            <th>Progress</th>",
        "            <th>Threshold</th>",
        "            <th>Missing Lines</th>",
        "        </tr>"
    ]
    
    # Sort modules by risk level (high->medium->low) and then by coverage (ascending)
    risk_order = {"high": 0, "medium": 1, "low": 2}
    sorted_modules = sorted(coverage_data["modules"], 
                           key=lambda x: (risk_order[x["risk_level"]], x["line_rate"]))
    
    for module in sorted_modules:
        risk_class = module["risk_level"]
        below_class = " below-threshold" if module["below_threshold"] else ""
        progress_width = min(100, int(module["line_rate"]))
        
        html.extend([
            f"        <tr class='{risk_class}{below_class}'>",
            f"            <td>{module['name']}</td>",
            f"            <td>{module['risk_level'].upper()}</td>",
            f"            <td>{module['line_rate']:.2f}%</td>",
            f"            <td><div class='progress-bar-container'><div class='progress-bar' style='width:{progress_width}px'></div></div></td>",
            f"            <td>{module['threshold']}%</td>",
            f"            <td>{len(module['missing_lines'])}</td>",
            "        </tr>"
        ])
    
    html.extend([
        "    </table>",
        
        "    <h2>Actionable Insights</h2>",
        "    <h3>Critical Gaps</h3>",
        "    <ul>"
    ])
    
    # High risk modules below threshold
    high_risk_below = [m for m in coverage_data["modules"] 
                      if m["risk_level"] == "high" and m["below_threshold"]]
    
    if high_risk_below:
        for module in high_risk_below:
            gap = module["threshold"] - module["line_rate"]
            html.append(f"        <li><strong>{module['name']}</strong>: {module['line_rate']:.2f}% " 
                      f"(gap: {gap:.2f}%, needs {len(module['missing_lines'])} more lines covered)</li>")
    else:
        html.append("        <li>No high-risk modules below threshold. Good job!</li>")
    
    html.extend([
        "    </ul>",
        "    <h3>Suggested Next Steps</h3>",
        "    <ol>",
        "        <li>Focus first on high-risk modules below threshold</li>",
        "        <li>Then address medium-risk modules with the largest coverage gaps</li>",
        "        <li>Review modules with many uncovered lines, even if percentage is acceptable</li>",
        "        <li>Consider adding more edge case and error handling tests</li>",
        "    </ol>",
        "</body>",
        "</html>"
    ])
    
    with open(output_file, "w") as f:
        f.write("\n".join(html))
    
    print(f"HTML report generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Analyze code coverage and identify gaps")
    parser.add_argument("--coverage-file", default="coverage.xml",
                        help="Path to coverage XML file (default: coverage.xml)")
    parser.add_argument("--html-output", default="coverage_analysis.html",
                        help="Output HTML report file (default: coverage_analysis.html)")
    parser.add_argument("--text-output", default="coverage_analysis.txt",
                        help="Output text report file (default: coverage_analysis.txt)")
    args = parser.parse_args()
    
    # Parse coverage data
    coverage_data = parse_coverage_xml(args.coverage_file)
    
    # Generate text report
    text_report = generate_text_report(coverage_data)
    with open(args.text_output, "w") as f:
        f.write(text_report)
    print(f"Text report generated: {args.text_output}")
    
    # Generate HTML report
    generate_html_report(coverage_data, args.html_output)
    
    # Print summary to console
    print("\nCOVERAGE ANALYSIS SUMMARY")
    print(f"Overall coverage: {coverage_data['project']['line_rate']:.2f}%")
    
    # Count modules below threshold by risk
    below_threshold = {
        "high": sum(1 for m in coverage_data["modules"] 
                    if m["risk_level"] == "high" and m["below_threshold"]),
        "medium": sum(1 for m in coverage_data["modules"] 
                     if m["risk_level"] == "medium" and m["below_threshold"]),
        "low": sum(1 for m in coverage_data["modules"] 
                  if m["risk_level"] == "low" and m["below_threshold"])
    }
    
    print(f"HIGH risk modules below threshold: {below_threshold['high']}")
    print(f"MEDIUM risk modules below threshold: {below_threshold['medium']}")
    print(f"LOW risk modules below threshold: {below_threshold['low']}")
    
    print(f"\nSee {args.text_output} and {args.html_output} for detailed analysis")

if __name__ == "__main__":
    main()
