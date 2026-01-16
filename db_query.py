#!/usr/bin/env python3
"""
Database Query Tool
Local file-based system for querying multiple databases.
Supports SQL Server (Windows Auth), Oracle, and more.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from db_connector import get_connector_from_config, load_config, create_connector


def format_value(value, max_width: int = 50) -> str:
    """Format a value for display."""
    if value is None:
        return 'NULL'
    if isinstance(value, float):
        # Format large numbers with commas
        if abs(value) >= 1000:
            return f"{value:,.2f}"
        return f"{value:.4f}"
    str_val = str(value)
    if len(str_val) > max_width:
        return str_val[:max_width-3] + '...'
    return str_val


def print_results_table(results: list, max_col_width: int = 40) -> None:
    """Print results in a formatted table."""
    if not results:
        print("(No results)")
        return

    # Get column names and calculate widths
    columns = list(results[0].keys())
    col_widths = {}

    for col in columns:
        col_widths[col] = min(
            max(
                len(col),
                max(len(format_value(row.get(col))) for row in results)
            ),
            max_col_width
        )

    # Print header
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)

    print(header)
    print(separator)

    # Print rows
    for row in results:
        row_str = " | ".join(
            format_value(row.get(col)).ljust(col_widths[col])
            for col in columns
        )
        print(row_str)


def print_results_json(results: list) -> None:
    """Print results as JSON."""
    print(json.dumps(results, indent=2, default=str))


def print_results_csv(results: list) -> None:
    """Print results as CSV."""
    if not results:
        return

    columns = list(results[0].keys())
    print(",".join(f'"{col}"' for col in columns))

    for row in results:
        values = []
        for col in columns:
            val = row.get(col)
            if val is None:
                values.append('')
            elif isinstance(val, str):
                values.append('"' + val.replace('"', '""') + '"')
            else:
                values.append(str(val))
        print(",".join(values))


def run_query(db_name: Optional[str], query: str, output_format: str = 'table',
              config_path: Optional[str] = None, verbose: bool = False) -> None:
    """Execute a query and display results."""
    try:
        connector = get_connector_from_config(db_name, config_path)

        if verbose:
            print(f"Database: {db_name or 'default'}")
            print(f"Connection: {connector.get_connection_string()}")
            print(f"Query: {query}")
            print("-" * 60)

        start_time = datetime.now()
        connector.connect()

        results = connector.execute_query(query)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        connector.disconnect()

        # Output results
        if output_format == 'json':
            print_results_json(results)
        elif output_format == 'csv':
            print_results_csv(results)
        else:
            print_results_table(results)

        if verbose:
            print("-" * 60)
            print(f"Rows returned: {len(results)}")
            print(f"Duration: {duration:.3f} seconds")

    except ImportError as e:
        print(f"Error: Missing required library - {e}", file=sys.stderr)
        print("\nTo install required libraries:", file=sys.stderr)
        print("  pip install pyodbc       # For SQL Server", file=sys.stderr)
        print("  pip install oracledb     # For Oracle", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def test_connection(db_name: Optional[str], config_path: Optional[str] = None) -> None:
    """Test database connection."""
    try:
        connector = get_connector_from_config(db_name, config_path)

        print(f"Testing connection to: {db_name or 'default'}")
        print(f"Connection string: {connector.get_connection_string()}")
        print()

        success, message = connector.test_connection()

        if success:
            print("SUCCESS: " + message)
        else:
            print("FAILED: " + message, file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def list_databases(config_path: Optional[str] = None) -> None:
    """List all configured databases."""
    try:
        config = load_config(config_path)
        default_db = config.get('default_database', '')

        print("Configured Databases:")
        print("-" * 60)

        for name, db_config in config.get('databases', {}).items():
            is_default = " (default)" if name == default_db else ""
            db_type = db_config.get('type', 'unknown')
            server = db_config.get('server') or db_config.get('host', 'unknown')
            database = db_config.get('database', '')
            desc = db_config.get('description', '')

            print(f"\n  {name}{is_default}")
            print(f"    Type: {db_type}")
            print(f"    Server: {server}")
            if database:
                print(f"    Database: {database}")
            if desc:
                print(f"    Description: {desc}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def save_query(name: str, query: str, db_name: Optional[str] = None,
               queries_path: Optional[str] = None) -> None:
    """Save a query to the saved queries file."""
    if queries_path is None:
        queries_path = Path(__file__).parent / 'saved_queries.json'

    queries_path = Path(queries_path)

    # Load existing queries
    if queries_path.exists():
        with open(queries_path, 'r') as f:
            queries = json.load(f)
    else:
        queries = {}

    # Save the query
    queries[name] = {
        'query': query,
        'database': db_name,
        'created': datetime.now().isoformat()
    }

    with open(queries_path, 'w') as f:
        json.dump(queries, f, indent=2)

    print(f"Query saved as '{name}'")


def run_saved_query(name: str, output_format: str = 'table',
                    queries_path: Optional[str] = None,
                    config_path: Optional[str] = None,
                    verbose: bool = False) -> None:
    """Run a previously saved query."""
    if queries_path is None:
        queries_path = Path(__file__).parent / 'saved_queries.json'

    queries_path = Path(queries_path)

    if not queries_path.exists():
        print("No saved queries found.", file=sys.stderr)
        sys.exit(1)

    with open(queries_path, 'r') as f:
        queries = json.load(f)

    if name not in queries:
        print(f"Query '{name}' not found. Available: {list(queries.keys())}", file=sys.stderr)
        sys.exit(1)

    query_info = queries[name]
    run_query(
        query_info.get('database'),
        query_info['query'],
        output_format,
        config_path,
        verbose
    )


def list_saved_queries(queries_path: Optional[str] = None) -> None:
    """List all saved queries."""
    if queries_path is None:
        queries_path = Path(__file__).parent / 'saved_queries.json'

    queries_path = Path(queries_path)

    if not queries_path.exists():
        print("No saved queries found.")
        return

    with open(queries_path, 'r') as f:
        queries = json.load(f)

    if not queries:
        print("No saved queries found.")
        return

    print("Saved Queries:")
    print("-" * 60)

    for name, info in queries.items():
        db = info.get('database', 'default')
        query = info.get('query', '')[:60]
        if len(info.get('query', '')) > 60:
            query += '...'
        print(f"\n  {name}")
        print(f"    Database: {db}")
        print(f"    Query: {query}")


def main():
    parser = argparse.ArgumentParser(
        description="Local database query tool - query multiple databases from a single interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "SELECT * FROM users LIMIT 10"
  %(prog)s -d sqlserver_budg "SELECT COUNT(*) FROM orders"
  %(prog)s --test                              # Test default connection
  %(prog)s --test -d oracle_hr                 # Test specific connection
  %(prog)s --list                              # List configured databases
  %(prog)s --format json "SELECT * FROM users" # Output as JSON
  %(prog)s --save myquery "SELECT * FROM users"
  %(prog)s --run myquery                       # Run saved query

Configuration:
  Edit db_config.json to add/modify database connections.
        """
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='SQL query to execute'
    )

    parser.add_argument(
        '-d', '--database',
        metavar='NAME',
        help='Database name from config (default: uses default_database)'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['table', 'json', 'csv'],
        default='table',
        help='Output format (default: table)'
    )

    parser.add_argument(
        '-c', '--config',
        metavar='PATH',
        help='Path to config file (default: db_config.json)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output including connection info and timing'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test database connection'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List configured databases'
    )

    parser.add_argument(
        '--save',
        metavar='NAME',
        help='Save the query with the given name'
    )

    parser.add_argument(
        '--run',
        metavar='NAME',
        help='Run a saved query by name'
    )

    parser.add_argument(
        '--list-queries',
        action='store_true',
        help='List saved queries'
    )

    args = parser.parse_args()

    # Handle commands
    if args.list:
        list_databases(args.config)
    elif args.test:
        test_connection(args.database, args.config)
    elif args.list_queries:
        list_saved_queries()
    elif args.run:
        run_saved_query(args.run, args.format, config_path=args.config, verbose=args.verbose)
    elif args.save and args.query:
        save_query(args.save, args.query, args.database)
    elif args.query:
        run_query(args.database, args.query, args.format, args.config, args.verbose)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
