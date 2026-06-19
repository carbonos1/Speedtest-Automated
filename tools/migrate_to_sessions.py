#!/usr/bin/env python3
"""Migrate legacy speedtest_results/iperf_results tables into the new
test_sessions + test_runs schema.

Legacy rows are grouped into sessions using a timestamp-gap heuristic:
consecutive rows closer than --gap-seconds (default 60s) belong to the
same session; a larger gap starts a new session.

USAGE
    # Dry-run: report proposed grouping, write nothing
    python tools/migrate_to_sessions.py

    # Apply migration after reviewing the dry-run
    python tools/migrate_to_sessions.py --apply

    # Custom gap threshold
    python tools/migrate_to_sessions.py --gap-seconds 30 --apply

After --apply, the legacy tables are renamed to *_legacy (kept for
verification) and can be dropped later once the new schema is confirmed.
"""
import argparse
import os
import sys
from collections import Counter

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrappers.database import get_connection, init_database

GAP_DEFAULT = 60  # seconds (speedtest)
IPERF_GAP_DEFAULT = 25  # seconds (iperf; intra-session spacing is ~20s)


def _parse_ts(value):
    """Parse a timestamp string to a timezone-naive pandas Timestamp, or NaT."""
    if value is None or value == '' or (isinstance(value, float) and pd.isna(value)):
        return pd.NaT
    return pd.to_datetime(value, errors='coerce', utc=True).tz_localize(None)


def _group_rows(df, ts_col, gap_seconds):
    """Split a timestamp-sorted DataFrame into session groups.

    Returns a list of DataFrames, one per proposed session.
    """
    df = df.copy()
    df['_ts'] = df[ts_col].apply(_parse_ts)
    df = df.sort_values('_ts').reset_index(drop=True)
    if df.empty:
        return []
    groups = []
    current = [0]
    for i in range(1, len(df)):
        prev_ts = df.loc[i - 1, '_ts']
        curr_ts = df.loc[i, '_ts']
        if pd.isna(prev_ts) or pd.isna(curr_ts):
            # Can't measure a gap; be conservative and start a new session
            groups.append(df.loc[current])
            current = [i]
            continue
        gap = (curr_ts - prev_ts).total_seconds()
        if gap > gap_seconds:
            groups.append(df.loc[current])
            current = [i]
        else:
            current.append(i)
    groups.append(df.loc[current])
    for g in groups:
        g.drop(columns=['_ts'], inplace=True)
    return groups


def _summarize_groups(all_groups, label):
    """Print a human-readable summary of proposed sessions for one table."""
    sizes = [len(g) for g in all_groups]
    dist = Counter(sizes)
    print(f'\n=== {label} ===')
    print(f'  total legacy rows : {sum(sizes)}')
    print(f'  proposed sessions : {len(all_groups)}')
    print('  runs-per-session distribution:')
    for size in sorted(dist):
        marker = '  <-- flagged (>10 runs)' if size > 10 else ''
        print(f'    {size} run(s): {dist[size]} session(s){marker}')
    if all_groups:
        sample = all_groups[0]
        ts_col = 'timestamp' if 'timestamp' in sample.columns else 'test_datetime'
        first = all_groups[0][ts_col].iloc[0]
        last = all_groups[-1][ts_col].iloc[-1]
        print(f'  time span         : {first}  ->  {last}')


def _insert_session_from_legacy(conn, group, mode):
    """Build and insert one test_sessions row + N test_runs rows from a
    legacy DataFrame group, computing averages on the fly."""
    is_speedtest = mode == 'speedtest'
    num_runs = len(group)

    if is_speedtest:
        ts_col = 'timestamp'
        server_id = int(group['server_id'].iloc[0]) if 'server_id' in group.columns else None
        server_name = group['server_name'].iloc[0] if 'server_name' in group.columns else None
        location = group['location'].iloc[0] if 'location' in group.columns else None
        client_ip = group['client_ip'].iloc[0] if 'client_ip' in group.columns else None
        num_streams_dl = None
        num_streams_ul = None
        dl = group['download_mbps']
        ul = group['upload_mbps']
        lat = group['latency'] if 'latency' in group.columns else pd.Series([None] * num_runs)
        idle = group['idle_jitter'] if 'idle_jitter' in group.columns else pd.Series([None] * num_runs)
        dlj = group['download_jitter'] if 'download_jitter' in group.columns else pd.Series([None] * num_runs)
        ulj = group['upload_jitter'] if 'upload_jitter' in group.columns else pd.Series([None] * num_runs)
        urls = group['result_url'] if 'result_url' in group.columns else pd.Series([None] * num_runs)
        nsdl = pd.Series([None] * num_runs)
        nsul = pd.Series([None] * num_runs)
    else:
        ts_col = 'test_datetime'
        server_id = None
        server_name = group['server_name'].iloc[0] if 'server_name' in group.columns else None
        location = None
        client_ip = None
        num_streams_dl = int(group['num_streams_dl'].iloc[0]) if 'num_streams_dl' in group.columns else None
        num_streams_ul = int(group['num_streams_ul'].iloc[0]) if 'num_streams_ul' in group.columns else None
        dl = group['download_mbps']
        ul = group['upload_mbps']
        lat = pd.Series([None] * num_runs)
        idle = pd.Series([None] * num_runs)
        dlj = pd.Series([None] * num_runs)
        ulj = pd.Series([None] * num_runs)
        urls = pd.Series([None] * num_runs)
        nsdl = group['num_streams_dl'] if 'num_streams_dl' in group.columns else pd.Series([None] * num_runs)
        nsul = group['num_streams_ul'] if 'num_streams_ul' in group.columns else pd.Series([None] * num_runs)

    run_ts = group[ts_col].tolist()
    started_at = run_ts[0] if run_ts else None
    completed_at = run_ts[-1] if run_ts else None

    def _mean(s):
        v = s.dropna()
        return float(v.mean()) if not v.empty else None

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
        mode, started_at, completed_at, num_runs,
        server_id, server_name, location, client_ip,
        num_streams_dl, num_streams_ul,
        _mean(dl), _mean(ul),
        _mean(lat), _mean(idle),
        _mean(dlj), _mean(ulj),
    ))
    session_id = cur.lastrowid

    dl_l = dl.tolist()
    ul_l = ul.tolist()
    lat_l = lat.tolist()
    idle_l = idle.tolist()
    dlj_l = dlj.tolist()
    ulj_l = ulj.tolist()
    nsdl_l = nsdl.tolist()
    nsul_l = nsul.tolist()
    url_l = urls.tolist()

    for i in range(num_runs):
        conn.execute('''
            INSERT INTO test_runs (
                session_id, run_number, run_timestamp,
                download_mbps, upload_mbps,
                latency, idle_jitter, download_jitter, upload_jitter,
                num_streams_dl, num_streams_ul, result_url, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id, i + 1, run_ts[i],
            dl_l[i], ul_l[i],
            lat_l[i], idle_l[i], dlj_l[i], ulj_l[i],
            nsdl_l[i], nsul_l[i], url_l[i], None,
        ))
    return session_id


def _table_exists(conn, name):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _legacy_has_data(conn):
    sp = conn.execute('SELECT COUNT(*) FROM speedtest_results').fetchone()[0] if _table_exists(conn, 'speedtest_results') else 0
    ip = conn.execute('SELECT COUNT(*) FROM iperf_results').fetchone()[0] if _table_exists(conn, 'iperf_results') else 0
    return sp, ip


def main():
    parser = argparse.ArgumentParser(
        description='Migrate legacy speedtest/iperf tables into the session/run schema'
    )
    parser.add_argument('--gap-seconds', type=float, default=GAP_DEFAULT,
                        help=f'Session split threshold in seconds for speedtest (default: {GAP_DEFAULT})')
    parser.add_argument('--iperf-gap-seconds', type=float, default=IPERF_GAP_DEFAULT,
                        help=f'Session split threshold in seconds for iperf '
                             f'(default: {IPERF_GAP_DEFAULT}; intra-session spacing ~20s)')
    parser.add_argument('--apply', action='store_true',
                        help='Perform the migration (default: dry-run only)')
    args = parser.parse_args()

    init_database()

    with get_connection() as conn:
        sp_count, ip_count = _legacy_has_data(conn)
        if sp_count == 0 and ip_count == 0:
            print('No legacy data to migrate (speedtest_results and iperf_results are empty/absent).')
            return

        # --- Read legacy data ---
        sp_groups, ip_groups = [], []
        if sp_count:
            sp_df = pd.read_sql_query('SELECT * FROM speedtest_results ORDER BY timestamp', conn)
            sp_groups = _group_rows(sp_df, 'timestamp', args.gap_seconds)
            _summarize_groups(sp_groups, 'speedtest_results')
        if ip_count:
            ip_df = pd.read_sql_query('SELECT * FROM iperf_results ORDER BY test_datetime', conn)
            ip_groups = _group_rows(ip_df, 'test_datetime', args.iperf_gap_seconds)
            _summarize_groups(ip_groups, 'iperf_results')

        total_sessions = len(sp_groups) + len(ip_groups)
        total_runs = sum(len(g) for g in sp_groups) + sum(len(g) for g in ip_groups)
        print('\n=== TOTALS ===')
        print(f'  proposed sessions : {total_sessions}')
        print(f'  total runs        : {total_runs}')

        if not args.apply:
            print('\nDRY RUN -- no data written. Re-run with --apply to migrate.')
            return

        # --- Apply: insert into new schema ---
        existing_sessions = conn.execute('SELECT COUNT(*) FROM test_sessions').fetchone()[0]
        if existing_sessions > 0:
            print(f'\nWARNING: test_sessions already has {existing_sessions} row(s). '
                  f'Migration will APPEND to existing data. Aborting to avoid duplicates. '
                  f'Clear test_sessions first if you want a clean migration.')
            return

        print('\nApplying migration...')
        sp_sessions = ip_sessions = 0
        for g in sp_groups:
            _insert_session_from_legacy(conn, g, 'speedtest')
            sp_sessions += 1
        for g in ip_groups:
            _insert_session_from_legacy(conn, g, 'iperf')
            ip_sessions += 1

        # --- Rename legacy tables ---
        if _table_exists(conn, 'speedtest_results'):
            conn.execute('ALTER TABLE speedtest_results RENAME TO speedtest_results_legacy')
            print('  Renamed speedtest_results -> speedtest_results_legacy')
        if _table_exists(conn, 'iperf_results'):
            conn.execute('ALTER TABLE iperf_results RENAME TO iperf_results_legacy')
            print('  Renamed iperf_results -> iperf_results_legacy')

        print(f'\nMigration complete: {sp_sessions} speedtest + {ip_sessions} iperf sessions '
              f'({total_runs} runs) inserted into test_sessions/test_runs.')
        print('Legacy tables renamed to *_legacy and can be dropped after verification.')


if __name__ == '__main__':
    main()
