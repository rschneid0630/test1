#!/usr/bin/env python3
"""
Database Connector Module
Provides unified interface for connecting to multiple database types.
Supports SQL Server, Oracle, and other databases.
"""

import json
import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import decimal


class DatabaseConnector(ABC):
    """Abstract base class for database connections."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        self.cursor = None

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the database."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close the database connection."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries."""
        pass

    @abstractmethod
    def get_connection_string(self) -> str:
        """Return the connection string (for display purposes)."""
        pass

    def test_connection(self) -> Tuple[bool, str]:
        """Test if connection can be established."""
        try:
            if self.connect():
                self.disconnect()
                return True, "Connection successful"
            return False, "Connection failed"
        except Exception as e:
            return False, str(e)


class SQLServerConnector(DatabaseConnector):
    """SQL Server database connector with Windows Authentication support."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.server = config.get('server', 'localhost')
        self.port = config.get('port', 1433)
        self.database = config.get('database', 'master')
        self.authentication = config.get('authentication', 'windows')
        self.username = config.get('username')
        self.password = config.get('password')
        self.driver = config.get('driver')

    def _get_driver(self) -> str:
        """Find available ODBC driver for SQL Server."""
        if self.driver:
            return self.driver

        import pyodbc
        drivers = pyodbc.drivers()

        # Preference order for SQL Server drivers
        preferred_drivers = [
            'ODBC Driver 18 for SQL Server',
            'ODBC Driver 17 for SQL Server',
            'ODBC Driver 13 for SQL Server',
            'SQL Server Native Client 11.0',
            'SQL Server Native Client 10.0',
            'SQL Server',
            'FreeTDS',
        ]

        for driver in preferred_drivers:
            if driver in drivers:
                return driver

        # Return first available driver that looks like SQL Server
        for driver in drivers:
            if 'sql' in driver.lower() or 'tds' in driver.lower():
                return driver

        raise RuntimeError(f"No SQL Server ODBC driver found. Available drivers: {drivers}")

    def get_connection_string(self) -> str:
        """Build and return the connection string."""
        driver = self._get_driver()

        if self.authentication == 'windows':
            # Windows Authentication (Trusted Connection)
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"Trusted_Connection=yes;"
            )
        else:
            # SQL Server Authentication
            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )

        # Add TrustServerCertificate for newer drivers
        if '17' in driver or '18' in driver:
            conn_str += "TrustServerCertificate=yes;"

        return conn_str

    def connect(self) -> bool:
        """Establish connection to SQL Server."""
        import pyodbc

        conn_str = self.get_connection_string()
        self.connection = pyodbc.connect(conn_str)
        self.cursor = self.connection.cursor()
        return True

    def disconnect(self) -> None:
        """Close the SQL Server connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries."""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        # Get column names
        columns = [column[0] for column in self.cursor.description] if self.cursor.description else []

        # Fetch all results
        rows = self.cursor.fetchall()

        # Convert to list of dictionaries
        results = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                # Handle special types
                if isinstance(value, decimal.Decimal):
                    row_dict[columns[i]] = float(value)
                elif isinstance(value, datetime):
                    row_dict[columns[i]] = value.isoformat()
                else:
                    row_dict[columns[i]] = value
            results.append(row_dict)

        return results

    def execute_scalar(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute a query and return single scalar value."""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        row = self.cursor.fetchone()
        if row:
            value = row[0]
            if isinstance(value, decimal.Decimal):
                return float(value)
            return value
        return None


class OracleConnector(DatabaseConnector):
    """Oracle database connector (placeholder for future implementation)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1521)
        self.service_name = config.get('service_name')
        self.sid = config.get('sid')
        self.username = config.get('username')
        self.password = config.get('password')

    def get_connection_string(self) -> str:
        """Build Oracle connection string."""
        if self.service_name:
            return f"{self.host}:{self.port}/{self.service_name}"
        elif self.sid:
            return f"{self.host}:{self.port}:{self.sid}"
        return f"{self.host}:{self.port}"

    def connect(self) -> bool:
        """Establish connection to Oracle."""
        import oracledb

        if self.service_name:
            dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
        else:
            dsn = oracledb.makedsn(self.host, self.port, sid=self.sid)

        self.connection = oracledb.connect(
            user=self.username,
            password=self.password,
            dsn=dsn
        )
        self.cursor = self.connection.cursor()
        return True

    def disconnect(self) -> None:
        """Close the Oracle connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """Execute a query and return results as list of dictionaries."""
        if not self.cursor:
            raise RuntimeError("Not connected to database")

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        columns = [col[0] for col in self.cursor.description] if self.cursor.description else []
        rows = self.cursor.fetchall()

        results = []
        for row in rows:
            row_dict = {}
            for i, value in enumerate(row):
                if isinstance(value, decimal.Decimal):
                    row_dict[columns[i]] = float(value)
                elif isinstance(value, datetime):
                    row_dict[columns[i]] = value.isoformat()
                else:
                    row_dict[columns[i]] = value
            results.append(row_dict)

        return results


def create_connector(db_type: str, config: Dict[str, Any]) -> DatabaseConnector:
    """Factory function to create appropriate database connector."""
    connectors = {
        'sqlserver': SQLServerConnector,
        'oracle': OracleConnector,
    }

    connector_class = connectors.get(db_type.lower())
    if not connector_class:
        raise ValueError(f"Unsupported database type: {db_type}. Supported: {list(connectors.keys())}")

    return connector_class(config)


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load database configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent / 'db_config.json'

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        return json.load(f)


def get_connector_from_config(db_name: Optional[str] = None, config_path: Optional[str] = None) -> DatabaseConnector:
    """Get a database connector from configuration file."""
    config = load_config(config_path)

    if db_name is None:
        db_name = config.get('default_database')

    if db_name not in config.get('databases', {}):
        available = list(config.get('databases', {}).keys())
        raise ValueError(f"Database '{db_name}' not found in config. Available: {available}")

    db_config = config['databases'][db_name]
    db_type = db_config.get('type', 'sqlserver')

    return create_connector(db_type, db_config)
