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
        # New session/run model: one test_sessions row per invocation,
        # N test_runs rows per session. Supersedes the legacy averaged tables.
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT,
                started_at TEXT,
                completed_at TEXT,
                num_runs INTEGER,
                server_id INTEGER,
                server_name TEXT,
                location TEXT,
                client_ip TEXT,
                num_streams_dl INTEGER,
                num_streams_ul INTEGER,
                avg_download_mbps REAL,
                avg_upload_mbps REAL,
                avg_latency REAL,
                avg_idle_jitter REAL,
                avg_download_jitter REAL,
                avg_upload_jitter REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                run_number INTEGER,
                run_timestamp TEXT,
                download_mbps REAL,
                upload_mbps REAL,
                latency REAL,
                idle_jitter REAL,
                download_jitter REAL,
                upload_jitter REAL,
                num_streams_dl INTEGER,
                num_streams_ul INTEGER,
                result_url TEXT,
                error TEXT,
                FOREIGN KEY (session_id) REFERENCES test_sessions(id) ON DELETE CASCADE
            )
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_runs_session ON test_runs(session_id)
        ''')
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_started ON test_sessions(started_at)
        ''')

def insert_speedtest(df):
    """Insert speedtest results into the database."""
    if df.empty:
        return
    if len(df) > 1:
        # Store only the average of all runs
        df = pd.DataFrame([{
            'Mode': df['Mode'].iloc[0] if 'Mode' in df.columns else 'SpeedTest',
            'Timestamp': df['Timestamp'].iloc[0] if 'Timestamp' in df.columns else None,
            'Server Id': df['Server Id'].iloc[0] if 'Server Id' in df.columns else None,
            'Server Name': df['Server Name'].iloc[0] if 'Server Name' in df.columns else None,
            'Location': df['Location'].iloc[0] if 'Location' in df.columns else None,
            'Client IP Address': df['Client IP Address'].iloc[0] if 'Client IP Address' in df.columns else None,
            'Download Bandwidth (Mbps)': df['Download Bandwidth (Mbps)'].mean() if 'Download Bandwidth (Mbps)' in df.columns else None,
            'Upload Bandwidth (Mbps)': df['Upload Bandwidth (Mbps)'].mean() if 'Upload Bandwidth (Mbps)' in df.columns else None,
            'Latency': df['Latency'].mean() if 'Latency' in df.columns else None,
            'Idle Jitter': df['Idle Jitter'].mean() if 'Idle Jitter' in df.columns else None,
            'Download Jitter': df['Download Jitter'].mean() if 'Download Jitter' in df.columns else None,
            'Upload Jitter': df['Upload Jitter'].mean() if 'Upload Jitter' in df.columns else None,
            'Result URL': df['Result URL'].iloc[0] if 'Result URL' in df.columns else None
        }])

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
    if df.empty:
        return
    if len(df) > 1:
        # Store only the average of all runs
        df = pd.DataFrame([{
            'Mode': df['Mode'].iloc[0] if 'Mode' in df.columns else 'iPerf3',
            'Server Name': df['Server Name'].iloc[0] if 'Server Name' in df.columns else None,
            'datetime': df['datetime'].iloc[0] if 'datetime' in df.columns else None,
            'Download Bandwidth (Mbps)': df['Download Bandwidth (Mbps)'].mean() if 'Download Bandwidth (Mbps)' in df.columns else None,
            'Upload Bandwidth (Mbps)': df['Upload Bandwidth (Mbps)'].mean() if 'Upload Bandwidth (Mbps)' in df.columns else None,
            'Number of Streams (DL)': int(df['Number of Streams (DL)'].iloc[0]) if 'Number of Streams (DL)' in df.columns else None,
            'Number of Streams (UL)': int(df['Number of Streams (UL)'].iloc[0]) if 'Number of Streams (UL)' in df.columns else None
        }])

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


def _normalize_mode(mode):
    """Normalize a mode label to the canonical lowercase form used in test_sessions."""
    if mode is None:
        return None
    m = str(mode).lower()
    if 's' in m and 'iperf' not in m:
        return 'speedtest'
    if 'i' in m:
        return 'iperf'
    return m


def insert_session(df, mode):
    """Insert a multi-run test session into the new session/run schema.

    Creates one test_sessions row (with pre-computed averages) and one
    test_runs row per DataFrame row, preserving every individual run.
    Replaces the legacy averaged insert_speedtest/insert_iperf behaviour.

    Expected DataFrame columns (mode-dependent, missing cols tolerated):
      speedtest: Timestamp, Server Id, Server Name, Location, Client IP Address,
                 Download Bandwidth (Mbps), Upload Bandwidth (Mbps), Latency,
                 Idle Jitter, Download Jitter, Upload Jitter, Result URL
      iperf:     datetime, Server Name, Download Bandwidth (Mbps),
                 Upload Bandwidth (Mbps), Number of Streams (DL), Number of Streams (UL)
    """
    if df is None or df.empty:
        return None

    norm_mode = _normalize_mode(mode)
    is_speedtest = norm_mode == 'speedtest'

    def _col(name):
        return df[name] if name in df.columns else pd.Series([None] * len(df))

    # Timestamps: prefer per-run timestamps, fall back to session time
    if is_speedtest:
        ts_col = 'Timestamp'
    else:
        ts_col = 'datetime'
    run_timestamps = _col(ts_col).tolist() if ts_col in df.columns else [None] * len(df)
    started_at = run_timestamps[0] if run_timestamps and run_timestamps[0] else None
    completed_at = run_timestamps[-1] if run_timestamps and run_timestamps[-1] else None

    num_runs = len(df)
    dl = _col('Download Bandwidth (Mbps)')
    ul = _col('Upload Bandwidth (Mbps)')

    # Mode-specific session attributes (take first row's identity fields)
    server_id = int(df['Server Id'].iloc[0]) if is_speedtest and 'Server Id' in df.columns else None
    server_name = df['Server Name'].iloc[0] if 'Server Name' in df.columns else None
    location = df['Location'].iloc[0] if is_speedtest and 'Location' in df.columns else None
    client_ip = df['Client IP Address'].iloc[0] if is_speedtest and 'Client IP Address' in df.columns else None
    num_streams_dl = None
    num_streams_ul = None
    if not is_speedtest:
        if 'Number of Streams (DL)' in df.columns:
            num_streams_dl = int(df['Number of Streams (DL)'].iloc[0])
        if 'Number of Streams (UL)' in df.columns:
            num_streams_ul = int(df['Number of Streams (UL)'].iloc[0])

    # Pre-computed averages on the session row
    def _mean(series):
        if series is None or series.dropna().empty:
            return None
        return float(series.mean())

    avg_dl = _mean(dl)
    avg_ul = _mean(ul)
    avg_latency = _mean(_col('Latency')) if is_speedtest else None
    avg_idle_jitter = _mean(_col('Idle Jitter')) if is_speedtest else None
    avg_dl_jitter = _mean(_col('Download Jitter')) if is_speedtest else None
    avg_ul_jitter = _mean(_col('Upload Jitter')) if is_speedtest else None

    with get_connection() as conn:
        cur = conn.execute('''
            INSERT INTO test_sessions (
                mode, started_at, completed_at, num_runs,
                server_id, server_name, location, client_ip,
                num_streams_dl, num_streams_ul,
                avg_download_mbps, avg_upload_mbps,
                avg_latency, avg_idle_jitter,
                avg_download_jitter, avg_upload_jitter
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            norm_mode, started_at, completed_at, num_runs,
            server_id, server_name, location, client_ip,
            num_streams_dl, num_streams_ul,
            avg_dl, avg_ul,
            avg_latency, avg_idle_jitter,
            avg_dl_jitter, avg_ul_jitter,
        ))
        session_id = cur.lastrowid

        # Insert every run verbatim
        dl_list = dl.tolist()
        ul_list = ul.tolist()
        lat_list = _col('Latency').tolist() if is_speedtest else [None] * num_runs
        idle_list = _col('Idle Jitter').tolist() if is_speedtest else [None] * num_runs
        dlj_list = _col('Download Jitter').tolist() if is_speedtest else [None] * num_runs
        ulj_list = _col('Upload Jitter').tolist() if is_speedtest else [None] * num_runs
        nsdl_list = _col('Number of Streams (DL)').tolist() if not is_speedtest else [None] * num_runs
        nsul_list = _col('Number of Streams (UL)').tolist() if not is_speedtest else [None] * num_runs
        url_list = _col('Result URL').tolist() if is_speedtest else [None] * num_runs

        for i in range(num_runs):
            conn.execute('''
                INSERT INTO test_runs (
                    session_id, run_number, run_timestamp,
                    download_mbps, upload_mbps,
                    latency, idle_jitter, download_jitter, upload_jitter,
                    num_streams_dl, num_streams_ul, result_url, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, i + 1, run_timestamps[i],
                dl_list[i], ul_list[i],
                lat_list[i], idle_list[i], dlj_list[i], ulj_list[i],
                nsdl_list[i], nsul_list[i], url_list[i], None,
            ))

    return session_id

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


def get_session_results(limit=None):
    """Retrieve all test sessions (one row per invocation) as a DataFrame.

    Returns pre-computed averages from test_sessions, with columns renamed
    to match the legacy dashboard contract so the graph/table code is
    unchanged. This is the session-level counterpart to get_all_results().
    """
    params = ()
    query = '''
        SELECT id as session_id, mode, started_at, completed_at, num_runs,
               server_id, server_name, location, client_ip,
               num_streams_dl, num_streams_ul,
               avg_download_mbps, avg_upload_mbps,
               avg_latency, avg_idle_jitter,
               avg_download_jitter, avg_upload_jitter,
               created_at
        FROM test_sessions
        ORDER BY started_at DESC
    '''
    if limit is not None:
        query += ' LIMIT ?'
        params = (limit,)
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_session_runs(session_id):
    """Retrieve all individual runs for a given session as a DataFrame."""
    with get_connection() as conn:
        return pd.read_sql_query(
            '''SELECT * FROM test_runs WHERE session_id = ?
               ORDER BY run_number ASC''',
            conn, params=(session_id,)
        )


def get_all_session_results():
    """Get combined session-level results for analysis, mirroring the
    dashboard contract produced by the legacy get_all_results().

    Returns a single DataFrame sorted by time with 'file' and 'datetime'
    helper columns and renamed bandwidth/jitter columns, ready for
    analysis.build_graph().
    """
    sessions = get_session_results()
    if sessions.empty:
        return sessions

    # Use started_at as the temporal anchor
    ts = pd.to_datetime(sessions['started_at'], errors='coerce', utc=True)
    sessions['datetime'] = ts.dt.strftime('%Y-%m-%d %H:%M:%S')
    sessions['file'] = ts.dt.strftime('%Y-%m-%d_%H-%M-%S')

    rename = {
        'avg_download_mbps': 'Download Bandwidth (Mbps)',
        'avg_upload_mbps': 'Upload Bandwidth (Mbps)',
        'avg_latency': 'Latency',
        'avg_idle_jitter': 'Idle Jitter',
        'avg_download_jitter': 'Download Jitter',
        'avg_upload_jitter': 'Upload Jitter',
    }
    sessions = sessions.rename(columns=rename)
    return sessions.sort_values('file').reset_index(drop=True)

def db_is_empty():
    """Check if the database has no data."""
    with get_connection() as conn:
        speedtest_count = conn.execute('SELECT COUNT(*) FROM speedtest_results').fetchone()[0]
        iperf_count = conn.execute('SELECT COUNT(*) FROM iperf_results').fetchone()[0]
        session_count = conn.execute('SELECT COUNT(*) FROM test_sessions').fetchone()[0]
        return speedtest_count == 0 and iperf_count == 0 and session_count == 0

def csv_files_exist(results_dir=None):
    """Check if there are any CSV files in the results directory."""
    import glob
    
    if results_dir is None:
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    
    csv_files = glob.glob(f'{results_dir}/**/*.csv', recursive=True)
    return len(csv_files) > 0

def migrate_csv_to_db(results_dir=None):
    """Migrate existing CSV files to the database using the session/run model.

    Each CSV file becomes one test_sessions row with N test_runs rows,
    preserving every individual run (no averaging). Fixes the legacy
    behaviour that collapsed multi-run CSVs into a single averaged row.
    """
    import glob
    
    if results_dir is None:
        results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
    
    csv_files = glob.glob(f'{results_dir}/**/*.csv', recursive=True)
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            if 'Timestamp' in df.columns:
                insert_session(df, 'speedtest')
                print(f'Migrated speedtest: {csv_file} ({len(df)} runs)')
            elif 'datetime' in df.columns:
                insert_session(df, 'iperf')
                print(f'Migrated iperf: {csv_file} ({len(df)} runs)')
        except Exception as e:
            print(f'Error migrating {csv_file}: {e}')

if __name__ == '__main__':
    init_database()
    print(f'Database initialized at: {DB_PATH}')