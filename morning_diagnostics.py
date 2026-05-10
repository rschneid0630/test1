#!/usr/bin/env python3
"""
Morning Diagnostics Processor
Scans, parses, and summarizes diagnostic log files from morning system checks.
"""

import os
import re
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict


# Recognized diagnostic file extensions
DIAGNOSTIC_EXTENSIONS = {".log", ".txt", ".diag", ".diagnostic", ".out", ".err", ".json", ".csv"}

# Severity patterns to search for in log files
SEVERITY_PATTERNS = {
    "CRITICAL": re.compile(r"\b(CRITICAL|FATAL|EMERGENCY)\b", re.IGNORECASE),
    "ERROR": re.compile(r"\b(ERROR|ERR|FAIL(?:ED|URE)?)\b", re.IGNORECASE),
    "WARNING": re.compile(r"\b(WARN(?:ING)?|CAUTION)\b", re.IGNORECASE),
    "INFO": re.compile(r"\b(INFO|NOTICE)\b", re.IGNORECASE),
}

# Common metric patterns (key=value or key: value)
METRIC_PATTERN = re.compile(
    r"(cpu[_ ]?usage|memory[_ ]?usage|disk[_ ]?usage|load[_ ]?average|uptime|temperature|"
    r"latency|response[_ ]?time|throughput|error[_ ]?rate|packet[_ ]?loss)"
    r"\s*[:=]\s*([\d.]+\s*%?)",
    re.IGNORECASE,
)

# Timestamp patterns for log lines
TIMESTAMP_PATTERNS = [
    re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"),
    re.compile(r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}"),
    re.compile(r"\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}"),
]


class DiagnosticFile:
    """Represents a single parsed diagnostic file."""

    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.name
        self.size = 0
        self.line_count = 0
        self.severity_counts = Counter()
        self.critical_lines = []
        self.error_lines = []
        self.warning_lines = []
        self.metrics = {}
        self.parse_errors = []
        self.is_json = False
        self.json_data = None

    def parse(self, max_lines=50000):
        """Parse the diagnostic file and extract information."""
        try:
            self.size = self.path.stat().st_size
        except OSError as e:
            self.parse_errors.append(f"Cannot stat file: {e}")
            return

        if self.path.suffix.lower() == ".json":
            self._parse_json()
        else:
            self._parse_text(max_lines)

    def _parse_json(self):
        """Parse a JSON diagnostic file."""
        self.is_json = True
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                self.json_data = json.load(f)
            self.line_count = 1

            # Extract severity info from JSON structure
            text_repr = json.dumps(self.json_data, default=str)
            for severity, pattern in SEVERITY_PATTERNS.items():
                count = len(pattern.findall(text_repr))
                if count:
                    self.severity_counts[severity] = count

            # Extract metrics from JSON
            self._extract_json_metrics(self.json_data)

        except json.JSONDecodeError as e:
            self.parse_errors.append(f"Invalid JSON: {e}")
            # Fall back to text parsing
            self.is_json = False
            self._parse_text(50000)
        except OSError as e:
            self.parse_errors.append(f"Cannot read file: {e}")

    def _extract_json_metrics(self, data, prefix=""):
        """Recursively extract metrics from JSON data."""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (int, float)):
                    normalized = key.lower().replace(" ", "_")
                    if any(
                        term in normalized
                        for term in [
                            "cpu", "memory", "disk", "load", "uptime",
                            "temperature", "latency", "response", "throughput",
                            "error_rate", "packet",
                        ]
                    ):
                        self.metrics[full_key] = value
                elif isinstance(value, (dict, list)):
                    self._extract_json_metrics(value, full_key)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._extract_json_metrics(item, f"{prefix}[{i}]")

    def _parse_text(self, max_lines):
        """Parse a text-based diagnostic file."""
        try:
            with open(self.path, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    if line_num > max_lines:
                        break
                    self.line_count = line_num
                    stripped = line.strip()
                    if not stripped:
                        continue

                    # Check severity
                    for severity, pattern in SEVERITY_PATTERNS.items():
                        if pattern.search(stripped):
                            self.severity_counts[severity] += 1
                            if severity == "CRITICAL" and len(self.critical_lines) < 20:
                                self.critical_lines.append((line_num, stripped))
                            elif severity == "ERROR" and len(self.error_lines) < 20:
                                self.error_lines.append((line_num, stripped))
                            elif severity == "WARNING" and len(self.warning_lines) < 10:
                                self.warning_lines.append((line_num, stripped))
                            break  # Count highest severity only

                    # Extract metrics
                    for match in METRIC_PATTERN.finditer(stripped):
                        key = match.group(1).strip().lower().replace(" ", "_")
                        value = match.group(2).strip()
                        self.metrics[key] = value

        except OSError as e:
            self.parse_errors.append(f"Cannot read file: {e}")

    @property
    def health_status(self):
        """Determine overall health based on severity counts."""
        if self.severity_counts["CRITICAL"] > 0:
            return "CRITICAL"
        if self.severity_counts["ERROR"] > 0:
            return "ERROR"
        if self.severity_counts["WARNING"] > 0:
            return "WARNING"
        return "OK"


class MorningDiagnosticsProcessor:
    """Processes a directory of morning diagnostic files."""

    def __init__(self, directory, hours_back=24):
        self.directory = Path(directory).resolve()
        self.hours_back = hours_back
        self.cutoff_time = datetime.now() - timedelta(hours=hours_back)
        self.diagnostic_files = []
        self.skipped_files = []
        self.scan_errors = []

    def discover_files(self, recursive=False):
        """Discover diagnostic files in the target directory."""
        if not self.directory.exists():
            self.scan_errors.append(f"Directory does not exist: {self.directory}")
            return

        if not self.directory.is_dir():
            self.scan_errors.append(f"Not a directory: {self.directory}")
            return

        if recursive:
            entries = self.directory.rglob("*")
        else:
            entries = self.directory.iterdir()

        for entry in entries:
            if not entry.is_file():
                continue

            # Check extension
            if entry.suffix.lower() not in DIAGNOSTIC_EXTENSIONS:
                self.skipped_files.append((str(entry), "unrecognized extension"))
                continue

            # Check modification time
            try:
                mtime = datetime.fromtimestamp(entry.stat().st_mtime)
                if mtime < self.cutoff_time:
                    self.skipped_files.append((str(entry), "older than cutoff"))
                    continue
            except OSError as e:
                self.scan_errors.append(f"Cannot stat {entry}: {e}")
                continue

            self.diagnostic_files.append(DiagnosticFile(entry))

        # Sort by name for consistent output
        self.diagnostic_files.sort(key=lambda d: d.name)

    def process_all(self, max_lines=50000):
        """Parse all discovered diagnostic files."""
        for diag in self.diagnostic_files:
            diag.parse(max_lines=max_lines)

    def get_summary(self):
        """Generate an aggregate summary across all files."""
        total_critical = sum(d.severity_counts["CRITICAL"] for d in self.diagnostic_files)
        total_errors = sum(d.severity_counts["ERROR"] for d in self.diagnostic_files)
        total_warnings = sum(d.severity_counts["WARNING"] for d in self.diagnostic_files)
        total_info = sum(d.severity_counts["INFO"] for d in self.diagnostic_files)
        total_lines = sum(d.line_count for d in self.diagnostic_files)
        total_size = sum(d.size for d in self.diagnostic_files)

        if total_critical > 0:
            overall_status = "CRITICAL"
        elif total_errors > 0:
            overall_status = "ERROR"
        elif total_warnings > 0:
            overall_status = "WARNING"
        else:
            overall_status = "OK"

        # Collect all metrics
        all_metrics = {}
        for diag in self.diagnostic_files:
            for key, value in diag.metrics.items():
                all_metrics.setdefault(key, []).append((diag.name, value))

        return {
            "overall_status": overall_status,
            "files_processed": len(self.diagnostic_files),
            "files_skipped": len(self.skipped_files),
            "total_lines": total_lines,
            "total_size": total_size,
            "total_critical": total_critical,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_info": total_info,
            "all_metrics": all_metrics,
        }

    def print_report(self, verbose=False):
        """Print the diagnostic report."""
        summary = self.get_summary()

        print("=" * 80)
        print("MORNING DIAGNOSTICS REPORT")
        print(f"Directory: {self.directory}")
        print(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Cutoff: files modified in the last {self.hours_back} hours")
        print("=" * 80)
        print()

        # Overall Status
        status = summary["overall_status"]
        status_indicator = {
            "OK": "[OK]",
            "WARNING": "[WARNING]",
            "ERROR": "[ERROR]",
            "CRITICAL": "[CRITICAL]",
        }
        print(f"OVERALL STATUS: {status_indicator.get(status, status)}")
        print("-" * 80)
        print(f"Files Processed:  {summary['files_processed']}")
        print(f"Files Skipped:    {summary['files_skipped']}")
        print(f"Total Lines:      {summary['total_lines']:,}")
        print(f"Total Size:       {self._format_size(summary['total_size'])}")
        print()

        # Severity Summary
        print("SEVERITY SUMMARY")
        print("-" * 80)
        print(f"  Critical:  {summary['total_critical']:,}")
        print(f"  Errors:    {summary['total_errors']:,}")
        print(f"  Warnings:  {summary['total_warnings']:,}")
        print(f"  Info:      {summary['total_info']:,}")
        print()

        # Per-File Breakdown
        if self.diagnostic_files:
            print("PER-FILE BREAKDOWN")
            print("-" * 80)
            print(f"{'File':<35} {'Status':<12} {'Critical':>8} {'Errors':>8} {'Warnings':>8} {'Lines':>8}")
            print("-" * 80)
            for diag in self.diagnostic_files:
                print(
                    f"{diag.name:<35} {diag.health_status:<12} "
                    f"{diag.severity_counts['CRITICAL']:>8} "
                    f"{diag.severity_counts['ERROR']:>8} "
                    f"{diag.severity_counts['WARNING']:>8} "
                    f"{diag.line_count:>8}"
                )
            print()

        # Critical and Error Details
        critical_files = [d for d in self.diagnostic_files if d.critical_lines]
        if critical_files:
            print("CRITICAL ISSUES")
            print("-" * 80)
            for diag in critical_files:
                print(f"  [{diag.name}]")
                for line_num, line in diag.critical_lines:
                    print(f"    Line {line_num}: {line[:120]}")
            print()

        error_files = [d for d in self.diagnostic_files if d.error_lines]
        if error_files:
            print("ERROR DETAILS")
            print("-" * 80)
            for diag in error_files:
                print(f"  [{diag.name}]")
                for line_num, line in diag.error_lines[:5]:
                    print(f"    Line {line_num}: {line[:120]}")
                remaining = len(diag.error_lines) - 5
                if remaining > 0:
                    print(f"    ... and {remaining} more error(s)")
            print()

        if verbose:
            warning_files = [d for d in self.diagnostic_files if d.warning_lines]
            if warning_files:
                print("WARNING DETAILS")
                print("-" * 80)
                for diag in warning_files:
                    print(f"  [{diag.name}]")
                    for line_num, line in diag.warning_lines:
                        print(f"    Line {line_num}: {line[:120]}")
                print()

        # Extracted Metrics
        if summary["all_metrics"]:
            print("EXTRACTED METRICS")
            print("-" * 80)
            for key, sources in sorted(summary["all_metrics"].items()):
                for filename, value in sources:
                    print(f"  {key:<30} {str(value):>15}  ({filename})")
            print()

        # Parse Errors
        all_parse_errors = []
        for diag in self.diagnostic_files:
            for err in diag.parse_errors:
                all_parse_errors.append((diag.name, err))

        if all_parse_errors or self.scan_errors:
            print("PROCESSING ERRORS")
            print("-" * 80)
            for err in self.scan_errors:
                print(f"  Scan: {err}")
            for filename, err in all_parse_errors:
                print(f"  Parse [{filename}]: {err}")
            print()

        if verbose and self.skipped_files:
            print("SKIPPED FILES")
            print("-" * 80)
            for filepath, reason in self.skipped_files:
                print(f"  {Path(filepath).name}: {reason}")
            print()

        print("=" * 80)

    def export_json(self, output_path):
        """Export the report as JSON."""
        summary = self.get_summary()
        report = {
            "report_time": datetime.now().isoformat(),
            "directory": str(self.directory),
            "hours_back": self.hours_back,
            "overall_status": summary["overall_status"],
            "summary": {
                "files_processed": summary["files_processed"],
                "files_skipped": summary["files_skipped"],
                "total_lines": summary["total_lines"],
                "total_size": summary["total_size"],
                "total_critical": summary["total_critical"],
                "total_errors": summary["total_errors"],
                "total_warnings": summary["total_warnings"],
                "total_info": summary["total_info"],
            },
            "files": [],
            "metrics": {
                key: [{"source": src, "value": val} for src, val in sources]
                for key, sources in summary["all_metrics"].items()
            },
        }

        for diag in self.diagnostic_files:
            file_entry = {
                "name": diag.name,
                "path": str(diag.path),
                "size": diag.size,
                "line_count": diag.line_count,
                "health_status": diag.health_status,
                "severity_counts": dict(diag.severity_counts),
                "metrics": diag.metrics,
                "critical_lines": [
                    {"line": num, "text": text} for num, text in diag.critical_lines
                ],
                "error_lines": [
                    {"line": num, "text": text} for num, text in diag.error_lines
                ],
                "parse_errors": diag.parse_errors,
            }
            report["files"].append(file_entry)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"JSON report exported to: {output_path}")

    @staticmethod
    def _format_size(size_bytes):
        """Convert bytes to human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main():
    parser = argparse.ArgumentParser(
        description="Process morning diagnostic files and generate a summary report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /var/log/diagnostics          # Process today's diagnostics
  %(prog)s -r /var/log                   # Recursively scan /var/log
  %(prog)s --hours 8 /tmp/diagnostics    # Only files from last 8 hours
  %(prog)s -v /var/log/diagnostics       # Verbose output with warnings
  %(prog)s --json report.json ./logs     # Export report as JSON
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing diagnostic files (default: current directory)",
    )

    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively scan subdirectories",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output including warnings and skipped files",
    )

    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        metavar="N",
        help="Only process files modified within the last N hours (default: 24)",
    )

    parser.add_argument(
        "--max-lines",
        type=int,
        default=50000,
        metavar="N",
        help="Maximum lines to read per file (default: 50000)",
    )

    parser.add_argument(
        "--json",
        metavar="OUTPUT",
        help="Export report as JSON to the specified file",
    )

    args = parser.parse_args()

    # Validate directory
    target = Path(args.directory)
    if not target.exists():
        print(f"Error: Path '{args.directory}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not target.is_dir():
        print(f"Error: Path '{args.directory}' is not a directory", file=sys.stderr)
        sys.exit(1)

    try:
        processor = MorningDiagnosticsProcessor(args.directory, hours_back=args.hours)
        processor.discover_files(recursive=args.recursive)

        if not processor.diagnostic_files:
            print(f"No diagnostic files found in {target.resolve()}")
            print(f"(Looking for files with extensions: {', '.join(sorted(DIAGNOSTIC_EXTENSIONS))})")
            print(f"(Modified within the last {args.hours} hours)")
            if processor.skipped_files:
                print(f"\nSkipped {len(processor.skipped_files)} file(s):")
                for filepath, reason in processor.skipped_files[:10]:
                    print(f"  {Path(filepath).name}: {reason}")
            sys.exit(0)

        processor.process_all(max_lines=args.max_lines)
        processor.print_report(verbose=args.verbose)

        if args.json:
            processor.export_json(args.json)

        # Exit with non-zero status if critical issues found
        summary = processor.get_summary()
        if summary["overall_status"] == "CRITICAL":
            sys.exit(2)
        elif summary["overall_status"] == "ERROR":
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
