'''Wrapper for Speedtest Executable.
This modules allows us to generate a speedtest.net result, and convert it into pandas dataframe'''
import os
import json
import subprocess
import pandas as pd


class Speedtest:
    """Main class for running Speedtest.net tests via the CLI binary.
    Converts results into Pandas DataFrames for downstream processing.
    """

    def speedtest_prefix(self):
        '''Build the speedtest CLI binary path for the current OS.'''
        if os.name == "nt":
            return f'"{os.path.dirname(os.path.dirname(__file__))}\\bin\\speedtest.exe"'
        elif os.name == "posix":
            return f'{os.path.dirname(os.path.dirname(__file__))}/bin/speedtest'
        raise RuntimeError(f'Unsupported OS: {os.name}')

    def run_test(self, server_name='Server:', server_id=14670, num_of_runs=6, timeout=120):
        '''Runs Speedtest tests and returns results as a Pandas DataFrame.

        Args:
            server_name: Name of the server passed (for display only).
            server_id: Speedtest.net server ID to test against.
            num_of_runs: Number of test iterations.
            timeout: Per-run timeout in seconds.

        Returns:
            DataFrame with one row per run.
        '''
        df_total = pd.DataFrame()
        for i in range(num_of_runs):
            print(f'Running {server_name} Speedtest #{i+1} ')
            df = self._run_single(server_id, timeout)
            print(df[['Server Name', 'Location', 'Download Bandwidth (Mbps)', 'Upload Bandwidth (Mbps)']])
            df_total = pd.concat([df_total, df], ignore_index=True)
        return df_total

    def _run_single(self, server_id, timeout):
        '''Execute a single speedtest run and parse the JSON output.'''
        cmd = f'{self.speedtest_prefix()} -s {server_id} -f json --accept-license'
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f'Speedtest timed out after {timeout}s for server {server_id}')
        except FileNotFoundError:
            raise RuntimeError('Speedtest binary not found. Ensure bin/speedtest exists.')

        if result.returncode != 0:
            stderr = result.stderr.strip() if result.stderr else 'unknown error'
            raise RuntimeError(f'Speedtest failed (exit {result.returncode}): {stderr}')

        return self.create_dataframe(result.stdout)

    def create_dataframe(self, input_str):
        '''Convert the speedtest JSON output string into a Pandas DataFrame.

        Guards against missing keys in the JSON response so a partial
        or unexpected payload doesn't crash with a bare KeyError.
        '''
        if not input_str or not input_str.strip():
            raise RuntimeError('Speedtest returned empty output')

        try:
            data = json.loads(input_str)
        except json.JSONDecodeError as e:
            raise RuntimeError(f'Failed to parse speedtest JSON: {e}')

        server = data.get('server', {})
        interface = data.get('interface', {})
        download = data.get('download', {})
        upload = data.get('upload', {})
        ping = data.get('ping', {})
        result_info = data.get('result', {})

        dl_bw = download.get('bandwidth')
        ul_bw = upload.get('bandwidth')

        df = pd.DataFrame({
            'Mode': 'SpeedTest',
            'Timestamp': [data.get('timestamp', '')],
            'Server Id': [server.get('id')],
            'Server Name': [server.get('name')],
            'Location': [server.get('location')],
            'Client IP Address': [interface.get('externalIp')],
            'Download Bandwidth (Mbps)': [dl_bw / 125000 if dl_bw else None],
            'Upload Bandwidth (Mbps)': [ul_bw / 125000 if ul_bw else None],
            'Latency': [ping.get('latency')],
            'Idle Jitter': [ping.get('jitter')],
            'Download Jitter': [download.get('latency', {}).get('jitter')],
            'Upload Jitter': [upload.get('latency', {}).get('jitter')],
            'Result URL': [result_info.get('url')],
        })
        return df
