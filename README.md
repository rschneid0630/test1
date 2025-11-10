# Filesystem Statistics Tool

A professional Python tool for analyzing and visualizing filesystem statistics with beautiful charts and HTML reports.

## Features

- **Comprehensive Statistics**: Total files, directories, sizes, and more
- **File Type Analysis**: Distribution of file types across your filesystem
- **Size Distribution**: Categorization of files by size ranges
- **Visual Analytics**: Professional charts and graphs using Matplotlib
- **HTML Reports**: Beautiful, responsive HTML reports with embedded charts
- **Largest Files/Directories**: Identify space hogs quickly
- **Recent Files Tracking**: See files modified in the last 30 days
- **Disk Usage**: Overall disk space utilization

## Installation

### Prerequisites

```bash
# Install matplotlib for visualizations
pip install matplotlib
```

### Basic Setup

The script is ready to use once you have Python 3.6+ and matplotlib installed.

## Usage

### Basic Commands

```bash
# Scan current directory with text output
./filesystem_stats.py

# Scan a specific directory
./filesystem_stats.py /path/to/directory

# Verbose output with additional details
./filesystem_stats.py -v

# Limit scan depth
./filesystem_stats.py --max-depth 3
```

### Generate Reports

```bash
# Generate HTML report with charts
./filesystem_stats.py --html report.html

# Generate HTML report for a specific directory
./filesystem_stats.py /home/user/Documents --html docs_report.html

# Generate report with verbose data
./filesystem_stats.py --html report.html -v

# Save individual chart images
./filesystem_stats.py --save-charts ./charts
```

### Advanced Examples

```bash
# Comprehensive analysis with HTML report
./filesystem_stats.py /var/log --html log_analysis.html -v

# Quick scan with limited depth
./filesystem_stats.py /home --max-depth 2 --html home_overview.html

# Follow symbolic links (use with caution)
./filesystem_stats.py --follow-symlinks --html full_scan.html
```

## Output

### Console Output

The tool provides a detailed text report including:
- Disk usage summary
- File and directory counts
- File type distribution (top 20)
- File size distribution
- Largest files (top 20)
- Largest directories (top 20, with -v)
- Recently modified files (with -v)
- Average statistics

### HTML Report

The HTML report includes:
- **Interactive Dashboard**: Summary cards with key metrics
- **Visual Charts**:
  - Disk usage pie chart
  - File and directory statistics bar chart
  - File type distribution pie chart
  - File size distribution bar chart
  - Largest files horizontal bar chart
- **Detailed Tables**:
  - File type breakdown with counts and percentages
  - Largest files with sizes and paths
- **Professional Design**: Responsive, modern UI with gradient styling

### Chart Images

Individual PNG charts can be saved separately:
- `disk_usage.png` - Disk space utilization
- `file_dir_stats.png` - Files vs directories comparison
- `file_types.png` - File extension distribution
- `size_distribution.png` - File size categories
- `largest_files.png` - Top largest files

## Example Screenshots

### HTML Report Preview

The generated HTML report features:
- Gradient header with report metadata
- Grid layout of summary statistics cards
- Embedded high-quality charts
- Sortable data tables
- Responsive design for mobile and desktop

### Sample Output

```
================================================================================
FILESYSTEM STATISTICS REPORT
Root Path: /home/user/test1
Scan Time: 2025-11-10 12:53:45
================================================================================

📊 DISK USAGE SUMMARY
--------------------------------------------------------------------------------
Total Disk Space:     1.82 TB
Used Space:           723.45 GB
Free Space:           1.10 TB
Disk Usage:           39.74%

Scanned Directory:    11.67 KB

📁 FILES AND DIRECTORIES
--------------------------------------------------------------------------------
Total Files:          1
Total Directories:    1
Hidden Files:         0
Hidden Directories:   1
Maximum Depth:        1

📄 FILE TYPE DISTRIBUTION (Top 20)
--------------------------------------------------------------------------------
.py                          1 (100.00%)
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `path` | Path to scan (default: current directory) |
| `-v, --verbose` | Show verbose output with additional details |
| `--max-depth N` | Maximum directory depth to scan |
| `--follow-symlinks` | Follow symbolic links (may cause infinite loops) |
| `--html FILE` | Generate HTML report with charts |
| `--save-charts DIR` | Save individual chart images to directory |

## Performance Tips

1. **Limit Depth**: Use `--max-depth` for faster scans on deep directory structures
2. **Avoid Symlinks**: Don't use `--follow-symlinks` unless necessary
3. **Large Filesystems**: Consider scanning specific subdirectories rather than root
4. **Network Drives**: May be slow; consider local directories first

## Troubleshooting

### Matplotlib Not Found

```
Warning: matplotlib not available. Install with: pip install matplotlib
Continuing with text-only output...
```

**Solution**: Install matplotlib:
```bash
pip install matplotlib
```

### Permission Errors

The tool will log permission errors but continue scanning accessible files.

### Large Filesystems

For very large filesystems (millions of files), consider:
- Using `--max-depth` to limit scope
- Scanning specific subdirectories
- Running during off-peak hours

## Technical Details

### Requirements
- Python 3.6+
- matplotlib (optional, for visualizations)

### File Size Categories
- 0 B (empty)
- < 1 KB
- 1 KB - 1 MB
- 1 MB - 10 MB
- 10 MB - 100 MB
- 100 MB - 1 GB
- \> 1 GB

### Data Collection
- Scans using `os.walk()` for efficient traversal
- Tracks top 20 largest files and directories
- Records files modified in last 30 days
- Calculates directory sizes recursively

## License

This tool is provided as-is for filesystem analysis and monitoring purposes.

## Contributing

Feel free to enhance this tool with additional features such as:
- JSON/CSV export options
- Custom file filters
- Duplicate file detection
- File age analysis
- More chart types
