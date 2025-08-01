#!/bin/python
'''Speedtest / iPerf3 Automation CLI. Marries the Libraries we have created together into something we can control with command flags'''
from datetime import datetime
import argparse
import os
import sys
from wrappers import Speedtest
from wrappers import Iperf3Auto

HELP = \
    f"\nSpeedTest-Automated\n"\
    f"2024 TOC\n"\
    f"-h --help\n"\
    f"-v --value\n"
TELSTRA_MELBOURNE = ['Telstra - Melbourne',12491]
TELSTRA_SYDNEY = ['Telstra - Sydney',12492]

def print_results(df_total,output_file):
    '''Prints output results of testing on screen, and saves them to a prefined CSV'''
    df_total.to_csv(f'{os.path.dirname(__file__)}/results/{output_file}')
    print(df_total[['Server Name','Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']])
    print('-------\nAverage\n-------')
    print(df_total[['Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']].mean())
    print('-------')
    print(f'Results Found in {output_file}')


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

    parser = argparse.ArgumentParser(
        description="Speedtest / iPerf3 Automation CLI"
    )
    parser.add_argument('-m', '--mode', choices=['speedtest', 'iperf'], default='speedtest',
                        help='Test mode: speedtest or iperf (default: speedtest)')
    parser.add_argument('-n', '--num-of-runs', type=int, default=3,
                        help='Number of runs (default: 3)')
    parser.add_argument('-s', '--server-id', type=str,
                        help='Server ID or IP address')
    parser.add_argument('-l', '--location', type=str,
                        help='Location shortcut (mel, syd, etc.)')
    parser.add_argument('-o', '--outputfile', type=str,
                        help='Output file name (without .csv)')

    args = parser.parse_args()

    # Defaults
    num_of_runs = args.num_of_runs
    mode = args.mode
    server = ['Telstra - Melbourne', 12491]

    # Handle location or server-id
    if args.location:
        if 'mel' in args.location.lower():
            server = ['Telstra - Melbourne', 12491]
        elif 'syd' in args.location.lower():
            server = ['Telstra - Sydney', 12492]
        else:
            print(f"Unknown location: {args.location}, using default.")
    if args.server_id:
        server = [f'Custom {mode.title()} Server', args.server_id]

    # Output file
    if args.outputfile:
        output_file = f'{args.outputfile}.csv'
    else:
        output_file = f'{mode.title()}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'

    # Run test and print results
    df = run_test(mode=mode, server=server, num_of_runs=num_of_runs)
    print_results(df_total=df, output_file=output_file)

if __name__ == "__main__":
    main()
