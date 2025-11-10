#!/usr/bin/env python3
"""
Filesystem Statistics Tool
Provides comprehensive statistics about a filesystem or directory with visualizations.
"""

import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import shutil
import base64
from io import BytesIO

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")
    print("Continuing with text-only output...\n")


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

    def create_visualizations(self):
        """Create visualization charts and return them as base64 encoded images."""
        if not MATPLOTLIB_AVAILABLE:
            return {}

        charts = {}

        # Set a professional style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')

        # 1. File Type Distribution (Pie Chart)
        if self.file_types:
            fig, ax = plt.subplots(figsize=(12, 8))

            # Get top 10 file types and group the rest as "Others"
            top_types = dict(self.file_types.most_common(10))
            other_count = sum(count for ext, count in self.file_types.items() if ext not in top_types)

            if other_count > 0:
                top_types['Others'] = other_count

            colors = plt.cm.Set3(range(len(top_types)))
            wedges, texts, autotexts = ax.pie(
                top_types.values(),
                labels=top_types.keys(),
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )

            # Make percentage text more readable
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)

            ax.set_title('File Type Distribution', fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()

            # Convert to base64
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['file_types'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

        # 2. File Size Distribution (Bar Chart)
        if self.size_distribution:
            fig, ax = plt.subplots(figsize=(12, 6))

            size_order = ["0 B (empty)", "< 1 KB", "1 KB - 1 MB", "1 MB - 10 MB",
                         "10 MB - 100 MB", "100 MB - 1 GB", "> 1 GB"]

            categories = [cat for cat in size_order if cat in self.size_distribution]
            counts = [self.size_distribution[cat] for cat in categories]

            bars = ax.bar(range(len(categories)), counts, color='steelblue', alpha=0.8)
            ax.set_xlabel('File Size Category', fontsize=12, fontweight='bold')
            ax.set_ylabel('Number of Files', fontsize=12, fontweight='bold')
            ax.set_title('File Size Distribution', fontsize=16, fontweight='bold', pad=20)
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=45, ha='right')

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height):,}',
                       ha='center', va='bottom', fontsize=9)

            ax.grid(axis='y', alpha=0.3)
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['size_distribution'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

        # 3. Largest Files (Horizontal Bar Chart)
        if self.largest_files:
            fig, ax = plt.subplots(figsize=(12, 8))

            files_to_show = min(15, len(self.largest_files))
            files = self.largest_files[:files_to_show]

            names = [Path(f[0]).name if len(Path(f[0]).name) < 30
                    else Path(f[0]).name[:27] + '...' for f in files]
            sizes_mb = [f[1] / (1024 * 1024) for f in files]  # Convert to MB

            y_pos = range(len(names))
            bars = ax.barh(y_pos, sizes_mb, color='coral', alpha=0.8)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(names)
            ax.invert_yaxis()
            ax.set_xlabel('File Size (MB)', fontsize=12, fontweight='bold')
            ax.set_title('Largest Files', fontsize=16, fontweight='bold', pad=20)

            # Add value labels
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f'{sizes_mb[i]:.2f} MB',
                       ha='left', va='center', fontsize=9, style='italic')

            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['largest_files'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

        # 4. File Count and Directory Count (Comparison Bar Chart)
        fig, ax = plt.subplots(figsize=(10, 6))

        categories = ['Total Files', 'Total Directories', 'Hidden Files', 'Hidden Directories']
        counts = [self.total_files, self.total_dirs, self.hidden_files, self.hidden_dirs]
        colors_list = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12']

        bars = ax.bar(categories, counts, color=colors_list, alpha=0.8)
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('File and Directory Statistics', fontsize=16, fontweight='bold', pad=20)
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=15, ha='right')

        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()

        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        charts['file_dir_stats'] = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()

        # 5. Disk Usage (if available)
        try:
            disk_usage = shutil.disk_usage(self.root_path)
            fig, ax = plt.subplots(figsize=(10, 6))

            used_gb = disk_usage.used / (1024**3)
            free_gb = disk_usage.free / (1024**3)

            categories = ['Used Space', 'Free Space']
            sizes = [used_gb, free_gb]
            colors_disk = ['#e74c3c', '#2ecc71']

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=categories,
                autopct='%1.1f%%',
                colors=colors_disk,
                startangle=90
            )

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(12)

            ax.set_title(f'Disk Usage (Total: {disk_usage.total / (1024**3):.2f} GB)',
                        fontsize=16, fontweight='bold', pad=20)
            plt.tight_layout()

            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['disk_usage'] = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
        except:
            pass

        return charts

    def generate_html_report(self, output_file='filesystem_report.html'):
        """Generate an HTML report with embedded charts."""
        charts = self.create_visualizations()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Filesystem Statistics Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }}

        .stat-card h3 {{
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .chart-container {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .chart-container img {{
            width: 100%;
            height: auto;
            border-radius: 5px;
        }}

        .info-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}

        .info-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        .info-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}

        .info-table tr:last-child td {{
            border-bottom: none;
        }}

        .info-table tr:hover {{
            background: #f8f9fa;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            background: #667eea;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Filesystem Statistics Report</h1>
            <div class="subtitle">
                <strong>Root Path:</strong> {self.root_path}<br>
                <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>

        <div class="content">
            <!-- Summary Statistics -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Files</h3>
                    <div class="value">{self.total_files:,}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Directories</h3>
                    <div class="value">{self.total_dirs:,}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Size</h3>
                    <div class="value">{self.format_size(self.total_size)}</div>
                </div>
                <div class="stat-card">
                    <h3>Average File Size</h3>
                    <div class="value">{self.format_size(self.total_size / self.total_files) if self.total_files > 0 else "N/A"}</div>
                </div>
            </div>
"""

        # Add charts
        if MATPLOTLIB_AVAILABLE and charts:
            html_content += """
            <div class="section">
                <h2>📈 Visual Analytics</h2>
"""

            if 'disk_usage' in charts:
                html_content += f"""
                <div class="chart-container">
                    <h3 style="margin-bottom: 15px; color: #333;">Disk Usage Overview</h3>
                    <img src="data:image/png;base64,{charts['disk_usage']}" alt="Disk Usage">
                </div>
"""

            if 'file_dir_stats' in charts:
                html_content += f"""
                <div class="chart-container">
                    <h3 style="margin-bottom: 15px; color: #333;">File and Directory Statistics</h3>
                    <img src="data:image/png;base64,{charts['file_dir_stats']}" alt="File and Directory Stats">
                </div>
"""

            if 'file_types' in charts:
                html_content += f"""
                <div class="chart-container">
                    <h3 style="margin-bottom: 15px; color: #333;">File Type Distribution</h3>
                    <img src="data:image/png;base64,{charts['file_types']}" alt="File Type Distribution">
                </div>
"""

            if 'size_distribution' in charts:
                html_content += f"""
                <div class="chart-container">
                    <h3 style="margin-bottom: 15px; color: #333;">File Size Distribution</h3>
                    <img src="data:image/png;base64,{charts['size_distribution']}" alt="Size Distribution">
                </div>
"""

            if 'largest_files' in charts:
                html_content += f"""
                <div class="chart-container">
                    <h3 style="margin-bottom: 15px; color: #333;">Largest Files</h3>
                    <img src="data:image/png;base64,{charts['largest_files']}" alt="Largest Files">
                </div>
"""

            html_content += """
            </div>
"""

        # Add file type table
        if self.file_types:
            html_content += """
            <div class="section">
                <h2>📄 File Type Details</h2>
                <table class="info-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>File Extension</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for i, (ext, count) in enumerate(self.file_types.most_common(20), 1):
                percentage = (count / self.total_files) * 100
                html_content += f"""
                        <tr>
                            <td><span class="badge">{i}</span></td>
                            <td><strong>{ext}</strong></td>
                            <td>{count:,}</td>
                            <td>{percentage:.2f}%</td>
                        </tr>
"""
            html_content += """
                    </tbody>
                </table>
            </div>
"""

        # Add largest files table
        if self.largest_files:
            html_content += """
            <div class="section">
                <h2>🗂️ Largest Files</h2>
                <table class="info-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>File Path</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for i, (filepath, size) in enumerate(self.largest_files[:20], 1):
                try:
                    rel_path = Path(filepath).relative_to(self.root_path)
                except:
                    rel_path = filepath
                html_content += f"""
                        <tr>
                            <td><span class="badge">{i}</span></td>
                            <td><code>{rel_path}</code></td>
                            <td><strong>{self.format_size(size)}</strong></td>
                        </tr>
"""
            html_content += """
                    </tbody>
                </table>
            </div>
"""

        html_content += """
        </div>

        <div class="footer">
            Generated by Filesystem Statistics Tool |
            <strong>Python</strong> with <strong>Matplotlib</strong>
        </div>
    </div>
</body>
</html>
"""

        # Write HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Generate comprehensive filesystem statistics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Scan current directory
  %(prog)s /path/to/directory                 # Scan specific directory
  %(prog)s -v                                 # Verbose output with more details
  %(prog)s --max-depth 3                      # Limit scan depth
  %(prog)s --html report.html                 # Generate HTML report with charts
  %(prog)s --save-charts ./charts             # Save individual chart images
  %(prog)s --html report.html -v              # HTML report with verbose data
  %(prog)s /home --html home_stats.html       # Scan /home and create HTML report
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

    parser.add_argument(
        '--html',
        metavar='FILE',
        help='Generate HTML report with charts (e.g., report.html)'
    )

    parser.add_argument(
        '--save-charts',
        metavar='DIR',
        help='Save individual chart images to directory'
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

        # Generate HTML report if requested
        if args.html:
            if not MATPLOTLIB_AVAILABLE:
                print("\nWarning: Cannot generate HTML report without matplotlib", file=sys.stderr)
                print("Install with: pip install matplotlib", file=sys.stderr)
            else:
                print(f"\nGenerating HTML report...")
                output_file = stats.generate_html_report(args.html)
                print(f"HTML report saved to: {output_file}")

        # Save individual charts if requested
        if args.save_charts:
            if not MATPLOTLIB_AVAILABLE:
                print("\nWarning: Cannot save charts without matplotlib", file=sys.stderr)
                print("Install with: pip install matplotlib", file=sys.stderr)
            else:
                import os
                chart_dir = Path(args.save_charts)
                chart_dir.mkdir(parents=True, exist_ok=True)

                print(f"\nGenerating and saving charts to {chart_dir}...")
                charts = stats.create_visualizations()

                for chart_name, chart_data in charts.items():
                    chart_path = chart_dir / f"{chart_name}.png"
                    with open(chart_path, 'wb') as f:
                        f.write(base64.b64decode(chart_data))
                    print(f"  Saved: {chart_path}")

                print(f"Charts saved successfully!")

    except KeyboardInterrupt:
        print("\n\nScan interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
