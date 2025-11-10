#!/usr/bin/env python3
"""
Filesystem Statistics Tool
Provides comprehensive statistics about a filesystem or directory.
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import shutil


class FilesystemStats:
    def __init__(self, root_path="."):
        self.root_path = Path(root_path).resolve()
        self.total_files = 0
        self.total_dirs = 0
        self.total_size = 0
        self.file_types = Counter()
        self.size_distribution = defaultdict(int)
        self.largest_files = []
        self.largest_dirs = []
        self.hidden_files = 0
        self.hidden_dirs = 0
        self.recent_files = []
        self.max_depth = 0
        self.errors = []

    def get_file_extension(self, filename):
        """Get file extension or classify special files."""
        if filename.startswith('.'):
            return 'hidden/dotfile'
        ext = Path(filename).suffix.lower()
        return ext if ext else 'no extension'

    def format_size(self, size_bytes):
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def categorize_size(self, size_bytes):
        """Categorize file size into buckets."""
        if size_bytes == 0:
            return "0 B (empty)"
        elif size_bytes < 1024:
            return "< 1 KB"
        elif size_bytes < 1024 * 1024:
            return "1 KB - 1 MB"
        elif size_bytes < 1024 * 1024 * 10:
            return "1 MB - 10 MB"
        elif size_bytes < 1024 * 1024 * 100:
            return "10 MB - 100 MB"
        elif size_bytes < 1024 * 1024 * 1024:
            return "100 MB - 1 GB"
        else:
            return "> 1 GB"

    def scan_directory(self, max_depth=None, follow_symlinks=False):
        """Scan directory and collect statistics."""
        print(f"Scanning {self.root_path}...\n")

        for root, dirs, files in os.walk(self.root_path, followlinks=follow_symlinks):
            try:
                current_depth = len(Path(root).relative_to(self.root_path).parts)
                self.max_depth = max(self.max_depth, current_depth)

                if max_depth is not None and current_depth >= max_depth:
                    dirs.clear()
                    continue

                # Count directories
                for dir_name in dirs:
                    self.total_dirs += 1
                    if dir_name.startswith('.'):
                        self.hidden_dirs += 1

                    # Calculate directory size
                    dir_path = Path(root) / dir_name
                    try:
                        dir_size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                        self.largest_dirs.append((str(dir_path), dir_size))
                    except (PermissionError, OSError) as e:
                        self.errors.append(f"Cannot access directory {dir_path}: {e}")

                # Process files
                for filename in files:
                    self.total_files += 1
                    filepath = Path(root) / filename

                    try:
                        stat = filepath.stat()
                        file_size = stat.st_size
                        self.total_size += file_size

                        # Track file extension
                        ext = self.get_file_extension(filename)
                        self.file_types[ext] += 1

                        # Track size distribution
                        size_category = self.categorize_size(file_size)
                        self.size_distribution[size_category] += 1

                        # Track largest files
                        self.largest_files.append((str(filepath), file_size))

                        # Track hidden files
                        if filename.startswith('.'):
                            self.hidden_files += 1

                        # Track recent files (within last 30 days)
                        mtime = datetime.fromtimestamp(stat.st_mtime)
                        days_old = (datetime.now() - mtime).days
                        if days_old <= 30:
                            self.recent_files.append((str(filepath), mtime, file_size))

                    except (PermissionError, OSError, FileNotFoundError) as e:
                        self.errors.append(f"Cannot access file {filepath}: {e}")

            except Exception as e:
                self.errors.append(f"Error processing {root}: {e}")

        # Sort and limit lists
        self.largest_files.sort(key=lambda x: x[1], reverse=True)
        self.largest_files = self.largest_files[:20]

        self.largest_dirs.sort(key=lambda x: x[1], reverse=True)
        self.largest_dirs = self.largest_dirs[:20]

        self.recent_files.sort(key=lambda x: x[1], reverse=True)
        self.recent_files = self.recent_files[:20]

    def print_report(self, verbose=False):
        """Print comprehensive statistics report."""
        print("=" * 80)
        print(f"FILESYSTEM STATISTICS REPORT")
        print(f"Root Path: {self.root_path}")
        print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

        # Disk Usage Summary
        print("📊 DISK USAGE SUMMARY")
        print("-" * 80)
        try:
            disk_usage = shutil.disk_usage(self.root_path)
            print(f"Total Disk Space:     {self.format_size(disk_usage.total)}")
            print(f"Used Space:           {self.format_size(disk_usage.used)}")
            print(f"Free Space:           {self.format_size(disk_usage.free)}")
            print(f"Disk Usage:           {disk_usage.used / disk_usage.total * 100:.2f}%")
            print()
        except Exception as e:
            print(f"Cannot retrieve disk usage: {e}\n")

        print(f"Scanned Directory:    {self.format_size(self.total_size)}")
        print()

        # Files and Directories Count
        print("📁 FILES AND DIRECTORIES")
        print("-" * 80)
        print(f"Total Files:          {self.total_files:,}")
        print(f"Total Directories:    {self.total_dirs:,}")
        print(f"Hidden Files:         {self.hidden_files:,}")
        print(f"Hidden Directories:   {self.hidden_dirs:,}")
        print(f"Maximum Depth:        {self.max_depth}")
        print()

        # File Type Distribution
        if self.file_types:
            print("📄 FILE TYPE DISTRIBUTION (Top 20)")
            print("-" * 80)
            for ext, count in self.file_types.most_common(20):
                percentage = (count / self.total_files) * 100
                print(f"{ext:25s} {count:8,} ({percentage:5.2f}%)")
            print()

        # Size Distribution
        if self.size_distribution:
            print("📏 FILE SIZE DISTRIBUTION")
            print("-" * 80)
            size_order = ["0 B (empty)", "< 1 KB", "1 KB - 1 MB", "1 MB - 10 MB",
                         "10 MB - 100 MB", "100 MB - 1 GB", "> 1 GB"]
            for category in size_order:
                if category in self.size_distribution:
                    count = self.size_distribution[category]
                    percentage = (count / self.total_files) * 100
                    print(f"{category:20s} {count:8,} ({percentage:5.2f}%)")
            print()

        # Largest Files
        if self.largest_files:
            print("🗂️  LARGEST FILES (Top 20)")
            print("-" * 80)
            for i, (filepath, size) in enumerate(self.largest_files, 1):
                rel_path = Path(filepath).relative_to(self.root_path) if filepath.startswith(str(self.root_path)) else filepath
                print(f"{i:2d}. {self.format_size(size):>12s}  {rel_path}")
            print()

        # Largest Directories
        if self.largest_dirs and verbose:
            print("📂 LARGEST DIRECTORIES (Top 20)")
            print("-" * 80)
            for i, (dirpath, size) in enumerate(self.largest_dirs, 1):
                rel_path = Path(dirpath).relative_to(self.root_path) if dirpath.startswith(str(self.root_path)) else dirpath
                print(f"{i:2d}. {self.format_size(size):>12s}  {rel_path}")
            print()

        # Recent Files
        if self.recent_files and verbose:
            print("🕒 RECENTLY MODIFIED FILES (Last 30 Days, Top 20)")
            print("-" * 80)
            for i, (filepath, mtime, size) in enumerate(self.recent_files, 1):
                rel_path = Path(filepath).relative_to(self.root_path) if filepath.startswith(str(self.root_path)) else filepath
                print(f"{i:2d}. {mtime.strftime('%Y-%m-%d %H:%M')}  {self.format_size(size):>12s}  {rel_path}")
            print()

        # Errors
        if self.errors:
            print("⚠️  ERRORS ENCOUNTERED")
            print("-" * 80)
            for error in self.errors[:20]:
                print(f"  • {error}")
            if len(self.errors) > 20:
                print(f"  ... and {len(self.errors) - 20} more errors")
            print()

        # Average Statistics
        print("📈 AVERAGE STATISTICS")
        print("-" * 80)
        if self.total_files > 0:
            avg_file_size = self.total_size / self.total_files
            print(f"Average File Size:    {self.format_size(avg_file_size)}")
        if self.total_dirs > 0:
            avg_files_per_dir = self.total_files / self.total_dirs
            print(f"Average Files/Dir:    {avg_files_per_dir:.2f}")
        print()

        print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive filesystem statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Scan current directory
  %(prog)s /path/to/directory       # Scan specific directory
  %(prog)s -v                       # Verbose output with more details
  %(prog)s --max-depth 3            # Limit scan depth
  %(prog)s --follow-symlinks        # Follow symbolic links
        """
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to scan (default: current directory)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output including largest directories and recent files'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        metavar='N',
        help='Maximum directory depth to scan'
    )

    parser.add_argument(
        '--follow-symlinks',
        action='store_true',
        help='Follow symbolic links (may cause infinite loops)'
    )

    args = parser.parse_args()

    # Validate path
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"Error: Path '{args.path}' does not exist", file=sys.stderr)
        sys.exit(1)

    if not target_path.is_dir():
        print(f"Error: Path '{args.path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Run analysis
    try:
        stats = FilesystemStats(args.path)
        stats.scan_directory(max_depth=args.max_depth, follow_symlinks=args.follow_symlinks)
        stats.print_report(verbose=args.verbose)
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
