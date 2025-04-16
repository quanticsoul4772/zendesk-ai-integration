#!/usr/bin/env python3
"""
Legacy Component Reference Analyzer

This script analyzes the codebase to find references to legacy components
and helps plan their removal.

Usage:
    python analyze_legacy_references.py

Output:
    Creates a detailed report of all references to legacy components
"""

import os
import re
import csv
import argparse
from datetime import datetime
from collections import defaultdict

# Legacy components to analyze
LEGACY_COMPONENTS = [
    "ai_analyzer",
    "cache_manager",
    "db_repository",
    "report_generator",
    "modules.reporters",
    "scheduler",
    "webhook_server",
    "zendesk_client",
    "utils.service_provider",
]

# Files to ignore
IGNORE_DIRS = [
    ".git",
    "__pycache__",
    "venv",
    "backups",
    "node_modules",
]

class ReferenceAnalyzer:
    """Analyzes codebase for references to legacy components."""
    
    def __init__(self, root_dir, output_dir=None):
        """
        Initialize the analyzer.
        
        Args:
            root_dir: Root directory to analyze
            output_dir: Directory to store reports (default: root_dir)
        """
        self.root_dir = os.path.abspath(root_dir)
        self.output_dir = output_dir or self.root_dir
        self.references = defaultdict(list)
        self.dependency_map = defaultdict(set)
        
    def analyze(self):
        """Analyze the codebase for references to legacy components."""
        print(f"Analyzing codebase in {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            # Skip directories containing 'backups'
            if "backups" in root:
                continue
                
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        self._analyze_file(file_path)
                    except Exception as e:
                        print(f"Error analyzing {file_path}: {e}")
        
        print(f"Analysis complete. Found references in {len(self.references)} files.")
    
    def _analyze_file(self, file_path):
        """
        Analyze a single file for references to legacy components.
        
        Args:
            file_path: Path to the file to analyze
        """
        rel_path = os.path.relpath(file_path, self.root_dir)
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
            # For each legacy component, look for imports and references
            for component in LEGACY_COMPONENTS:
                # Look for imports
                import_patterns = [
                    rf"from\s+src\.modules\.{component}\s+import",
                    rf"from\s+modules\.{component}\s+import",
                    rf"import\s+src\.modules\.{component}",
                    rf"import\s+modules\.{component}",
                ]
                
                # Look for class or function references
                reference_patterns = [
                    rf"{component}\.",
                    rf"{component.split('.')[-1]}\.",
                ]
                
                # Check for matches
                for pattern in import_patterns + reference_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        line_start = content[:match.start()].rfind("\n") + 1
                        line_end = content.find("\n", match.end())
                        if line_end == -1:
                            line_end = len(content)
                        
                        line = content[line_start:line_end].strip()
                        line_num = content[:match.start()].count("\n") + 1
                        
                        self.references[rel_path].append({
                            "component": component,
                            "line": line_num,
                            "text": line,
                            "type": "import" if "import" in pattern else "reference"
                        })
                        
                        # Add to dependency map if it's an import
                        if "import" in pattern:
                            importing_module = rel_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                            if importing_module != component:
                                self.dependency_map[importing_module].add(component)
    
    def generate_report(self):
        """Generate reports based on the analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create CSV report
        csv_path = os.path.join(self.output_dir, f"legacy_references_{timestamp}.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["File", "Component", "Line", "Type", "Text"])
            
            for file_path, references in self.references.items():
                for ref in references:
                    writer.writerow([
                        file_path,
                        ref["component"],
                        ref["line"],
                        ref["type"],
                        ref["text"]
                    ])
        
        # Create summary report
        summary_path = os.path.join(self.output_dir, f"legacy_summary_{timestamp}.txt")
        with open(summary_path, "w", encoding="utf-8") as summary_file:
            summary_file.write("Legacy Component Reference Summary\n")
            summary_file.write("===============================\n\n")
            
            # Overall statistics
            total_references = sum(len(refs) for refs in self.references.values())
            summary_file.write(f"Total Files with References: {len(self.references)}\n")
            summary_file.write(f"Total References: {total_references}\n\n")
            
            # Per-component statistics
            component_stats = defaultdict(int)
            for references in self.references.values():
                for ref in references:
                    component_stats[ref["component"]] += 1
            
            summary_file.write("References by Component:\n")
            for component, count in sorted(component_stats.items(), key=lambda x: x[1], reverse=True):
                summary_file.write(f"  {component}: {count}\n")
            
            # Detailed breakdown by file
            summary_file.write("\nDetailed Breakdown by File:\n")
            for file_path, references in sorted(self.references.items()):
                summary_file.write(f"\n{file_path}:\n")
                
                # Group by component
                by_component = defaultdict(list)
                for ref in references:
                    by_component[ref["component"]].append(ref)
                
                for component, refs in sorted(by_component.items()):
                    summary_file.write(f"  {component}: {len(refs)} references\n")
                    for ref in sorted(refs, key=lambda x: x["line"]):
                        summary_file.write(f"    Line {ref['line']}: {ref['text'][:80]}{'...' if len(ref['text']) > 80 else ''}\n")
        
        # Create dependency graph report
        dep_path = os.path.join(self.output_dir, f"dependency_graph_{timestamp}.txt")
        with open(dep_path, "w", encoding="utf-8") as dep_file:
            dep_file.write("Legacy Component Dependency Graph\n")
            dep_file.write("===============================\n\n")
            
            for module, dependencies in sorted(self.dependency_map.items()):
                if dependencies:
                    dep_file.write(f"{module} depends on:\n")
                    for dep in sorted(dependencies):
                        dep_file.write(f"  {dep}\n")
                    dep_file.write("\n")
        
        print(f"Reports generated:")
        print(f"  CSV Report: {csv_path}")
        print(f"  Summary Report: {summary_path}")
        print(f"  Dependency Graph: {dep_path}")
        
        return {
            "csv_report": csv_path,
            "summary_report": summary_path,
            "dependency_graph": dep_path
        }

def main():
    parser = argparse.ArgumentParser(description="Analyze legacy component references")
    parser.add_argument("--root-dir", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      help="Root directory of the codebase to analyze")
    parser.add_argument("--output-dir", help="Directory to store reports")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if args.output_dir and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    analyzer = ReferenceAnalyzer(args.root_dir, args.output_dir)
    analyzer.analyze()
    analyzer.generate_report()

if __name__ == "__main__":
    main()
