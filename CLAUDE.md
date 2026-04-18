# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a filesystem statistics and analysis tool written in Python. The tool scans directories, collects comprehensive statistics about files and directories, and generates professional reports with visualizations.

## Prerequisites

```bash
pip install matplotlib
```

Matplotlib is required for chart generation and HTML report creation. The tool will run in text-only mode if matplotlib is not available.

## Running the Tool

### Basic Usage

```bash
# Scan current directory with text output
./filesystem_stats.py

# Scan specific directory
./filesystem_stats.py /path/to/directory

# Generate HTML report with embedded charts
./filesystem_stats.py --html report.html

# Save individual chart images
./filesystem_stats.py --save-charts ./charts

# Verbose output (includes largest directories and recent files)
./filesystem_stats.py -v

# Limit scan depth
./filesystem_stats.py --max-depth 3
```

## Code Architecture

### Main Components

**FilesystemStats Class** (`filesystem_stats.py`):
- Core analysis engine that walks directory trees and collects statistics
- Tracks file types, sizes, largest files/directories, recent modifications
- Maintains in-memory counters and sorted lists during scanning
- Uses `os.walk()` for efficient traversal with configurable depth and symlink handling

**Visualization System**:
- `create_visualizations()` - Generates 5 chart types using matplotlib
- Charts are created as PNG images encoded to base64 for HTML embedding
- Non-interactive backend (Agg) for server/headless environments
- Chart types: pie (file types, disk usage), bar (size distribution, file/dir stats), horizontal bar (largest files)

**HTML Report Generation**:
- `generate_html_report()` - Creates self-contained HTML with embedded charts
- Uses inline CSS with gradient styling and responsive design
- All charts embedded as base64 data URIs (no external files)
- Includes summary cards, detailed tables, and visual analytics section

### Data Flow

1. **Scanning**: `scan_directory()` walks the tree, collecting stats into instance variables
2. **Processing**: Data is sorted/filtered (top 20 lists, size categorization)
3. **Visualization**: Charts generated from processed data and encoded to base64
4. **Output**: Either text report to console or HTML file with embedded visualizations

### Key Design Decisions

- **Base64 Encoding**: Charts embedded in HTML to create single-file reports (no external dependencies)
- **Top-N Lists**: Limited to 20 items to prevent memory issues on large filesystems
- **Size Categorization**: Fixed buckets (< 1KB, 1KB-1MB, etc.) for consistent size distribution analysis
- **Error Handling**: Permission errors logged but don't stop scanning; allows partial results from restricted filesystems

## Output Files

Generated files (ignored by git):
- `*.html` - HTML reports with embedded charts
- `charts/*.png` - Individual chart images when using --save-charts
- `filesystem_report.html` - Default HTML output filename

## Important Notes

**This repository does NOT contain**:
- Bill processing/tracking system
- Neo4j database or "brain" system
- Any financial data management tools

If you need to work with bill processing or Neo4j databases, those systems are in a different repository or environment, not here.
