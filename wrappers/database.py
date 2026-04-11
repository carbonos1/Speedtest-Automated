"""SQLite Database wrapper for speedtest and iperf results."""
import sqlite3
import os
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results', 'speedtest.db')

@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize the database with tables if they don't exist."""
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS speedtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT DEFAULT 'SpeedTest',
                timestamp TEXT,
                server_id INTEGER,
                server_name TEXT,
                location TEXT,
                client_ip TEXT,
                download_mbps REAL,
                upload_mbps REAL,
                latency REAL,
                idle_jitter REAL,
                download_jitter REAL,
                upload_jitter REAL,
                result_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS iperf_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT DEFAULT 'iPerf3',
                server_name TEXT,
                test_datetime TEXT,
                download_mbps REAL,
                upload_mbps REAL,
                num_streams_dl INTEGER,
                num_streams_ul INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_speedtest_timestamp ON speedtest_results(timestamp)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_iperf_datetime ON iperf_results(test_datetime)
        ''')

def insert_speedtest(df):
    """Insert speedtest results into the database."""
    with get_connection() as conn:
        for _, row in df.iterrows():
            conn.execute('''
                INSERT INTO speedtest_results (
                    mode, timestamp, server_id, server_name, location,
                    client_ip, download_mbps, upload_mbps, latency,
                    idle_jitter, download_jitter, upload_jitter, result_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Mode', 'SpeedTest'),
                row.get('Timestamp'),
                row.get('Server Id'),
                row.get('Server Name'),
                row.get('Location'),
                row.get('Client IP Address'),
                row.get('Download Bandwidth (Mbps)'),
                row.get('Upload Bandwidth (Mbps)'),
                row.get('Latency'),
                row.get('Idle Jitter'),
                row.get('Download Jitter'),
                row.get('Upload Jitter'),
                row.get('Result URL')
            ))

def insert_iperf(df):
    """Insert iperf results into the database."""
    with get_connection() as conn:
        for _, row in df.iterrows():
            conn.execute('''
                INSERT INTO iperf_results (
                    mode, server_name, test_datetime, download_mbps,
                    upload_mbps, num_streams_dl, num_streams_ul
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                row.get('Mode', 'iPerf3'),
                row.get('Server Name'),
                row.get('datetime'),
                row.get('Download Bandwidth (Mbps)'),
                row.get('Upload Bandwidth (Mbps)'),
                row.get('Number of Streams (DL)'),
                row.get('Number of Streams (UL)')
            ))

def get_speedtest_results(limit=None):
    """Retrieve speedtest results as a DataFrame."""
    query = 'SELECT * FROM speedtest_results ORDER BY timestamp DESC'
    if limit:
        query += f' LIMIT {limit}'
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_iperf_results(limit=None):
    """Retrieve iperf results as a DataFrame."""
    query = 'SELECT * FROM iperf_results ORDER BY test_datetime DESC'
    if limit:
        query += f' LIMIT {limit}'
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)

def get_all_results():
    """Get combined results from both tables for analysis."""
    speedtest = get_speedtest_results()
    speedtest['datetime'] = pd.to_datetime(speedtest['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    speedtest['file'] = pd.to_datetime(speedtest['timestamp']).dt.strftime('%Y-%m-%d_%H-%M-%S')
    
    iperf = get_iperf_results()
    iperf['datetime'] = pd.to_datetime(iperf['test_datetime']).dt.strftime('%Y-%m-%d %H:%M:%S')
    iperf['file'] = pd.to_datetime(iperf['test_datetime']).dt.strftime('%Y-%m-%d_%H-%M-%S')
    
    return speedtest, iperf

def get_summary_by_server():
    """Get summary statistics grouped by server name."""
    with get_connection() as conn:
        speedtest = pd.read_sql_query('''
            SELECT server_name,
                   AVG(download_mbps) as "Download Bandwidth (Mbps)",
                   AVG(upload_mbps) as "Upload Bandwidth (Mbps)",
                   AVG(latency) as "Latency",
                   AVG(idle_jitter) as "Idle Jitter",
                   AVG(download_jitter) as "Download Jitter",
                   AVG(upload_jitter) as "Upload Jitter"
            FROM speedtest_results
            GROUP BY server_name
        ''', conn)
        
        iperf = pd.read_sql_query('''
            SELECT server_name,
                   AVG(download_mbps) as "Download Bandwidth (Mbps)",
                   AVG(upload_mbps) as "Upload Bandwidth (Mbps)"
            FROM iperf_results
            GROUP BY server_name
        ''', conn)
        
    return speedtest, iperf

def migrate_csv_to_db(results_dir=None):
    """Migrate existing CSV files to the database."""
    import glob
    
    if results_dir is None:
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    
    csv_files = glob.glob(f'{results_dir}/**/*.csv', recursive=True)
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            if 'Timestamp' in df.columns:
                insert_speedtest(df)
                print(f'Migrated speedtest: {csv_file}')
            elif 'datetime' in df.columns:
                insert_iperf(df)
                print(f'Migrated iperf: {csv_file}')
        except Exception as e:
            print(f'Error migrating {csv_file}: {e}')

if __name__ == '__main__':
    init_database()
    print(f'Database initialized at: {DB_PATH}')