'''Module to batch run iPerf tests using the iperf3 library.'''
import logging
from datetime import datetime

import iperf3
import pandas as pd

from wrappers.utils import bps_to_mbps

logger = logging.getLogger(__name__)


class Iperf3Auto:
    """Batch-run iPerf3 tests, mimicking the Speedtest class interface.

    Returns pandas DataFrames compatible with insert_session(df, 'iperf').
    """

    def __init__(self) -> None:
        pass

    def iperf_test(self, server: str, duration: int, reverse: bool) -> pd.DataFrame:
        '''Run a single iPerf3 test and return a one-row DataFrame.'''
        client = iperf3.Client()
        client.server_hostname = server
        client.duration = duration
        client.reverse = reverse
        client.num_streams = 10
        result = client.run()
        if result.error:
            raise RuntimeError(f'iPerf3 error: {result.error}')

        df = pd.DataFrame([result.__dict__])
        df = df.filter(['timesecs', 'num_streams', 'sent_bps', 'received_bps'])
        df['datetime'] = datetime.fromtimestamp(df.loc[0, 'timesecs'])
        df['sent_mbps'] = round(bps_to_mbps(df['sent_bps']), 2)
        df['received_mbps'] = round(bps_to_mbps(df['received_bps']), 2)
        df = df.drop(['sent_bps', 'received_bps', 'timesecs'], axis=1)
        return df

    def run_test(self, server: str, num_of_runs: int = 3) -> pd.DataFrame:
        '''Run download + upload iPerf3 tests for num_of_runs iterations.

        Returns a DataFrame with one row per iteration, compatible with
        insert_session(df, 'iperf').
        '''
        dfs = []
        for i in range(num_of_runs):
            logger.info(f'Running {server}: iPerf {i + 1}')

            df_download = self.iperf_test(server, 10, True)
            df_upload = self.iperf_test(server, 10, False)

            df_combo = pd.DataFrame()
            df_combo.loc[0, 'Mode'] = 'iPerf3'
            df_combo.loc[0, 'Server Name'] = f'{server}'
            df_combo['datetime'] = df_upload['datetime']
            df_combo['Download Bandwidth (Mbps)'] = df_download['received_mbps']
            df_combo['Upload Bandwidth (Mbps)'] = df_upload['received_mbps']
            df_combo['Number of Streams (DL)'] = df_download['num_streams']
            df_combo['Number of Streams (UL)'] = df_upload['num_streams']

            print(df_combo[['Server Name', 'Download Bandwidth (Mbps)', 'Upload Bandwidth (Mbps)']])
            dfs.append(df_combo)

        return pd.concat(dfs, ignore_index=True)
