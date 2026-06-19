"""Unit tests for the speedtest wrapper."""
import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrappers.speedtest_auto import Speedtest


def _mock_speedtest_json():
    return json.dumps({
        'timestamp': '2026-06-19T10:00:00Z',
        'server': {'id': 12491, 'name': 'Telstra - Melbourne', 'location': 'Melbourne'},
        'interface': {'externalIp': '14.201.187.93'},
        'download': {'bandwidth': 6250000, 'latency': {'jitter': 40.0}},
        'upload': {'bandwidth': 1187500, 'latency': {'jitter': 20.0}},
        'ping': {'latency': 5.0, 'jitter': 1.0},
        'result': {'url': 'https://www.speedtest.net/result/c/123'},
    })


class TestCreateDataframe:
    def test_valid_json(self):
        s = Speedtest()
        df = s.create_dataframe(_mock_speedtest_json())
        assert len(df) == 1
        assert df['Server Name'].iloc[0] == 'Telstra - Melbourne'
        assert df['Download Bandwidth (Mbps)'].iloc[0] == pytest.approx(50.0)
        assert df['Upload Bandwidth (Mbps)'].iloc[0] == pytest.approx(9.5)
        assert df['Latency'].iloc[0] == 5.0
        assert df['Result URL'].iloc[0] == 'https://www.speedtest.net/result/c/123'

    def test_empty_input_raises(self):
        s = Speedtest()
        with pytest.raises(RuntimeError, match='empty output'):
            s.create_dataframe('')

    def test_whitespace_input_raises(self):
        s = Speedtest()
        with pytest.raises(RuntimeError, match='empty output'):
            s.create_dataframe('   ')

    def test_invalid_json_raises(self):
        s = Speedtest()
        with pytest.raises(RuntimeError, match='Failed to parse'):
            s.create_dataframe('not json at all')

    def test_missing_keys_handled(self):
        s = Speedtest()
        partial = json.dumps({'timestamp': '2026-01-01T00:00:00Z'})
        df = s.create_dataframe(partial)
        assert df['Timestamp'].iloc[0] == '2026-01-01T00:00:00Z'
        assert pd.isna(df['Download Bandwidth (Mbps)'].iloc[0])
        assert df['Server Name'].iloc[0] is None

    def test_missing_bandwidth_handled(self):
        s = Speedtest()
        data = json.dumps({
            'timestamp': '2026-01-01T00:00:00Z',
            'server': {'id': 1, 'name': 'Test', 'location': 'TestCity'},
            'interface': {'externalIp': '1.2.3.4'},
            'download': {},
            'upload': {},
            'ping': {},
            'result': {},
        })
        df = s.create_dataframe(data)
        assert pd.isna(df['Download Bandwidth (Mbps)'].iloc[0])
        assert pd.isna(df['Upload Bandwidth (Mbps)'].iloc[0])
