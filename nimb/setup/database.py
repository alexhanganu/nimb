# -*- coding: utf-8 -*-
"""
This module contains all functions for interacting with the
NIMB credentials database (SQLite).
"""
import sqlite3
from os import path, environ
import sys

TABLES = {
    'remotes': ('id', 'username', 'host', 'password'),
}

def _get_db_path():
    """Returns the platform-specific path to the database file."""
    home_dir = environ.get('HOME') or environ.get('USERPROFILE')
    credentials_home = path.join(home_dir, ".nimb")
    return path.join(credentials_home, f"{sys.platform}.db")

def _connect_db():
    """Connects to the SQLite database."""
    return sqlite3.connect(_get_db_path(), check_same_thread=False)

def get_table_data(table_name, entry_id):
    """
    Retrieves data for a specific entry or all entries from a table.
    
    Args:
        table_name (str): The name of the table (e.g., 'remotes').
        entry_id (str): The ID of the entry to fetch, or 'all'.
        
    Returns:
        A dictionary containing the requested data.
    """
    conn = _connect_db()
    cursor = conn.cursor()
    table_data = {}
    
    query = f"SELECT * FROM {table_name}"
    if entry_id != 'all':
        query += f" WHERE id = ?"
        params = (entry_id,)
    else:
        params = ()

    try:
        data = cursor.execute(query, params).fetchall()
        col_names = TABLES[table_name]
        
        for row in data:
            row_id = row[0]
            table_data[row_id] = {col_names[i]: val for i, val in enumerate(row)}
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
        
    return table_data

def set_table_data(table_name, data_dict):
    """
    Inserts a new record or updates an existing one in the specified table.
    
    Args:
        table_name (str): The name of the table.
        data_dict (dict): A dictionary where keys are column names and values are the data.
                          Must include an 'id' key.
    """
    conn = _connect_db()
    cursor = conn.cursor()
    
    entry_id = data_dict.get('id')
    if not entry_id:
        print("Error: 'id' key is required in data_dict.")
        return

    try:
        # Check if entry exists
        cursor.execute(f"SELECT count(*) FROM {table_name} WHERE id = ?", (entry_id,))
        exists = cursor.fetchone()[0] != 0
        
        columns = list(data_dict.keys())
        values = list(data_dict.values())
        
        if exists:
            set_clause = ", ".join([f"{col} = ?" for col in columns if col != 'id'])
            sql = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
            params = [v for k, v in data_dict.items() if k != 'id'] + [entry_id]
        else:
            placeholders = ", ".join(["?"] * len(columns))
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            params = values

        cursor.execute(sql, params)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()