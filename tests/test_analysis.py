"""Unit tests for the analysis module."""
import os
import sys
import tempfile
from unittest.mock import patch

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.analysis import build_graph, get_results_summary
from wrappers import database


@pytest.fixture
def temp_db_with_data():
    """Set up a temp DB with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        with patch.object(database, 'DB_PATH', db_path):
            database.init_database()
            for i in range(3):
                df = pd.DataFrame({
                    'Mode': ['SpeedTest'],
                    'Timestamp': [f'2026-06-1{i}T10:00:00Z'],
                    'Server Id': [12491],
                    'Server Name': ['Telstra - Melbourne'],
                    'Location': ['Melbourne'],
                    'Client IP Address': ['1.2.3.4'],
                    'Download Bandwidth (Mbps)': [500.0 + i * 10],
                    'Upload Bandwidth (Mbps)': [95.0],
                    'Latency': [5.0],
                    'Idle Jitter': [1.0],
                    'Download Jitter': [40.0],
                    'Upload Jitter': [20.0],
                    'Result URL': [f'https://speedtest.net/{i}'],
                })
                database.insert_session(df, 'speedtest')
            yield db_path


class TestGetResultsSummary:
    def test_empty_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'empty.db')
            with patch.object(database, 'DB_PATH', db_path):
                database.init_database()
                result = get_results_summary()
                assert result.empty

    def test_returns_sessions(self, temp_db_with_data):
        result = get_results_summary()
        assert len(result) == 3
        assert 'Download Bandwidth (Mbps)' in result.columns
        assert 'Upload Bandwidth (Mbps)' in result.columns
        assert 'file' in result.columns

    def test_sorted_by_file(self, temp_db_with_data):
        result = get_results_summary()
        files = result['file'].tolist()
        assert files == sorted(files)


class TestBuildGraph:
    def test_builds_figure(self, temp_db_with_data):
        result = get_results_summary()
        fig = build_graph(result)
        assert len(fig.data) == 5
        assert fig.data[0].name == 'Download (in Mbps)'
        assert fig.data[1].name == 'Upload (in Mbps)'

    def test_empty_dataframe(self):
        build_graph(pd.DataFrame())
        # Should handle gracefully (may raise or return empty figure)
