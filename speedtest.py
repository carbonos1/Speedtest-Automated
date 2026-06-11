#!/bin/python
'''Speedtest / iPerf3 Automation CLI. Marries the Libraries we have created together into something we can control with command flags'''
from datetime import datetime
import argparse
import os
import sys
from wrappers import Speedtest
from wrappers import Iperf3Auto
from wrappers.database import init_database, insert_speedtest, insert_iperf, db_is_empty, csv_files_exist, migrate_csv_to_db

HELP = \
    f"\nSpeedTest-Automated\n"\
    f"2024 TOC\n"\
    f"-h --help\n"\
    f"-v --value\n"
TELSTRA_MELBOURNE = ['Telstra - Melbourne',12491]
TELSTRA_SYDNEY = ['Telstra - Sydney',12492]

def print_results(df_total, mode):
    '''Prints output results of testing on screen, and saves them to the SQLite database'''
    if 's' in mode.lower():
        insert_speedtest(df_total)
    else:
        insert_iperf(df_total)
    
    print(df_total[['Server Name','Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']])
    print('-------\nAverage\n-------')
    print(df_total[['Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']].mean())
    print('-------')
    print(f'Results saved to SQLite database')


def run_test(mode='speedtest',server=['Telstra - Melbourne',12491],num_of_runs=3):
    '''Function to run the Actual Tests'''

    if 's' in mode.lower():
        df = Speedtest().run_test(server_name=server[0],server_id=server[1],num_of_runs=num_of_runs)
    elif 'i' in mode.lower():
        df = Iperf3Auto().run_test(server=server[1],num_of_runs=num_of_runs)
    else:
        print(f"Unknown mode: {mode}. Please use 'speedtest' or 'iperf'.")
        sys.exit(1)

    return df


def main():
    '''Primary Function of Script, controls cli control logic, and interprets flags for our use :)'''
    init_database()
    
    if db_is_empty() and csv_files_exist():
        print('First run detected - migrating legacy CSV files to SQLite...')
        migrate_csv_to_db()
        print('Migration complete.')

    parser = argparse.ArgumentParser(
        description="Speedtest / iPerf3 Automation CLI"
    )
    parser.add_argument('-m', '--mode', choices=['speedtest', 'iperf', 's', 'i'], default='speedtest',
                        help='Test mode: speedtest or iperf (default: speedtest)')
    parser.add_argument('-n', '--num-of-runs', type=int, default=3,
                        help='Number of runs (default: 3)')
    parser.add_argument('-s', '--server-id', type=str,
                        help='Server ID or IP address')
    parser.add_argument('-l', '--location', type=str,
                        help='Location shortcut (mel, syd, etc.)')

    args = parser.parse_args()

    num_of_runs = args.num_of_runs
    mode = args.mode
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

    df = run_test(mode=mode, server=server, num_of_runs=num_of_runs)
    print_results(df_total=df, mode=mode)

if __name__ == "__main__":
    main()
