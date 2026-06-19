"""Unit tests for the database wrapper."""
import os
import sys
import tempfile
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrappers import database


@pytest.fixture
def temp_db():
    """Use a temporary database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        with patch.object(database, 'DB_PATH', db_path):
            database.init_database()
            yield db_path


def _mock_speedtest_df(num_runs=3):
    """Create a mock speedtest DataFrame matching the wrapper output format."""
    rows = []
    for i in range(num_runs):
        rows.append({
            'Mode': 'SpeedTest',
            'Timestamp': f'2026-06-19T10:00:{i:02d}Z',
            'Server Id': 12491,
            'Server Name': 'Telstra - Melbourne',
            'Location': 'Melbourne',
            'Client IP Address': '1.2.3.4',
            'Download Bandwidth (Mbps)': 500.0 + i * 10,
            'Upload Bandwidth (Mbps)': 95.0 + i,
            'Latency': 5.0 + i * 0.5,
            'Idle Jitter': 1.0,
            'Download Jitter': 40.0,
            'Upload Jitter': 20.0,
            'Result URL': f'https://speedtest.net/result/{i}',
        })
    return pd.DataFrame(rows)


def _mock_iperf_df(num_runs=3):
    """Create a mock iperf DataFrame matching the wrapper output format."""
    rows = []
    for i in range(num_runs):
        rows.append({
            'Mode': 'iPerf3',
            'datetime': f'2026-06-19 10:00:{i:02d}',
            'Server Name': '192.168.1.1',
            'Download Bandwidth (Mbps)': 400.0 + i * 20,
            'Upload Bandwidth (Mbps)': 350.0 + i * 15,
            'Number of Streams (DL)': 10,
            'Number of Streams (UL)': 10,
        })
    return pd.DataFrame(rows)


class TestInitDatabase:
    def test_creates_tables(self, temp_db):
        import sqlite3
        conn = sqlite3.connect(temp_db)
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )]
        assert 'test_sessions' in tables
        assert 'test_runs' in tables
        conn.close()

    def test_idempotent(self, temp_db):
        database.init_database()
        database.init_database()


class TestInsertSession:
    def test_speedtest_insert(self, temp_db):
        df = _mock_speedtest_df(num_runs=3)
        sid = database.insert_session(df, 'speedtest')
        assert sid is not None

        sessions = database.get_session_results()
        assert len(sessions) == 1
        assert sessions.iloc[0]['mode'] == 'speedtest'
        assert sessions.iloc[0]['num_runs'] == 3
        assert sessions.iloc[0]['avg_download_mbps'] == pytest.approx(510.0)
        assert sessions.iloc[0]['avg_upload_mbps'] == pytest.approx(96.0)

    def test_iperf_insert(self, temp_db):
        df = _mock_iperf_df(num_runs=4)
        sid = database.insert_session(df, 'iperf')
        assert sid is not None

        sessions = database.get_session_results()
        assert len(sessions) == 1
        assert sessions.iloc[0]['mode'] == 'iperf'
        assert sessions.iloc[0]['num_runs'] == 4

    def test_tr143_insert(self, temp_db):
        df = pd.DataFrame({
            'Mode': ['TR143'],
            'datetime': ['2026-06-19T11:00:00'],
            'Server Name': ['test.example.com'],
            'Download Bandwidth (Mbps)': [100.0],
            'Upload Bandwidth (Mbps)': [50.0],
            'Latency': [12.5],
        })
        sid = database.insert_session(df, 'tr143')
        assert sid is not None
        sessions = database.get_session_results()
        assert len(sessions) == 1
        assert sessions.iloc[0]['avg_latency'] == 12.5

    def test_empty_df_returns_none(self, temp_db):
        assert database.insert_session(pd.DataFrame(), 'speedtest') is None

    def test_runs_preserved(self, temp_db):
        df = _mock_speedtest_df(num_runs=5)
        sid = database.insert_session(df, 'speedtest')
        runs = database.get_session_runs(sid)
        assert len(runs) == 5
        assert runs['run_number'].tolist() == [1, 2, 3, 4, 5]
        assert runs['download_mbps'].tolist() == [500.0, 510.0, 520.0, 530.0, 540.0]

    def test_multiple_sessions(self, temp_db):
        df1 = _mock_speedtest_df(num_runs=3)
        df2 = _mock_iperf_df(num_runs=2)
        database.insert_session(df1, 'speedtest')
        database.insert_session(df2, 'iperf')
        sessions = database.get_session_results()
        assert len(sessions) == 2


class TestDbIsEmpty:
    def test_empty_db(self, temp_db):
        assert database.db_is_empty() is True

    def test_with_data(self, temp_db):
        df = _mock_speedtest_df()
        database.insert_session(df, 'speedtest')
        assert database.db_is_empty() is False


class TestNormalizeMode:
    def test_speedtest(self):
        assert database._normalize_mode('speedtest') == 'speedtest'
        assert database._normalize_mode('SpeedTest') == 'speedtest'

    def test_iperf(self):
        assert database._normalize_mode('iperf') == 'iperf'
        assert database._normalize_mode('iPerf3') == 'iperf'

    def test_tr143(self):
        assert database._normalize_mode('tr143') == 'tr143'

    def test_none(self):
        assert database._normalize_mode(None) is None
