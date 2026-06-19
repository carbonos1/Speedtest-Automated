#!/bin/python
'''Speedtest / iPerf3 / TR-143 Automation CLI. Marries the Libraries we have created together into something we can control with command flags'''
import argparse
import sys

from wrappers import Iperf3Auto, Speedtest, TR143Tester
from wrappers.database import csv_files_exist, db_is_empty, init_database, insert_session, migrate_csv_to_db


def print_results(df_total, mode):
    '''Prints output results of testing on screen, and saves them to the SQLite database'''
    insert_session(df_total, mode)

    print(df_total[['Server Name', 'Download Bandwidth (Mbps)', 'Upload Bandwidth (Mbps)']])
    print('-------\nAverage\n-------')
    print(df_total[['Download Bandwidth (Mbps)', 'Upload Bandwidth (Mbps)']].mean())
    print('-------')
    print('Results saved to SQLite database')


def run_test(mode='speedtest', server=None, num_of_runs=3,
             download_url=None, upload_url=None, upload_file=None, ping_host='google.com'):
    '''Function to run the Actual Tests'''
    if server is None:
        server = ['Telstra - Melbourne', 12491]

    if mode == 'speedtest':
        df = Speedtest().run_test(server_name=server[0], server_id=server[1], num_of_runs=num_of_runs)
    elif mode == 'iperf':
        df = Iperf3Auto().run_test(server=server[1], num_of_runs=num_of_runs)
    elif mode == 'tr143':
        tester = TR143Tester(
            download_url=download_url or '',
            upload_url=upload_url or '',
            upload_file_path=upload_file or '',
            ping_host=ping_host,
        )
        df = tester.run_test(num_of_runs=num_of_runs)
    else:
        print(f"Unknown mode: {mode}. Please use 'speedtest', 'iperf', or 'tr143'.")
        sys.exit(1)

    return df


def main():
    '''Primary Function of Script, controls cli control logic, and interprets flags for our use'''
    init_database()

    if db_is_empty() and csv_files_exist():
        print('First run detected - migrating legacy CSV files to SQLite...')
        migrate_csv_to_db()
        print('Migration complete.')

    parser = argparse.ArgumentParser(
        description="Speedtest / iPerf3 / TR-143 Automation CLI"
    )
    parser.add_argument('-m', '--mode', choices=['speedtest', 'iperf', 'tr143', 's', 'i'],
                        default='speedtest',
                        help='Test mode: speedtest, iperf, or tr143 (default: speedtest)')
    parser.add_argument('-n', '--num-of-runs', type=int, default=3,
                        help='Number of runs (default: 3)')
    parser.add_argument('-s', '--server-id', type=str,
                        help='Server ID or IP address (speedtest/iperf)')
    parser.add_argument('-l', '--location', type=str,
                        help='Location shortcut: mel or syd (speedtest)')
    parser.add_argument('--download-url', type=str,
                        help='Download URL for TR-143 mode')
    parser.add_argument('--upload-url', type=str,
                        help='Upload URL for TR-143 mode')
    parser.add_argument('--upload-file', type=str,
                        help='Path to file for TR-143 upload test')
    parser.add_argument('--ping-host', type=str, default='google.com',
                        help='Host for TR-143 latency measurement (default: google.com)')

    args = parser.parse_args()

    num_of_runs = args.num_of_runs
    mode = 'speedtest' if args.mode == 's' else 'iperf' if args.mode == 'i' else args.mode
    server = ['Telstra - Melbourne', 12491]

    if args.location:
        if 'mel' in args.location.lower():
            server = ['Telstra - Melbourne', 12491]
        elif 'syd' in args.location.lower():
            server = ['Telstra - Sydney', 12492]
        else:
            print(f"Unknown location: {args.location}, using default.")
    if args.server_id:
        server = [f'Custom {mode.title()} Server', args.server_id]

    df = run_test(
        mode=mode, server=server, num_of_runs=num_of_runs,
        download_url=args.download_url, upload_url=args.upload_url,
        upload_file=args.upload_file, ping_host=args.ping_host,
    )
    print_results(df_total=df, mode=mode)


if __name__ == "__main__":
    main()
