#!/bin/python
'''Speedtest / iPerf3 Automation CLI. Marries the Libraries we have created together into something we can control with command flags'''
from datetime import datetime
import getopt
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
    df_total.to_csv(f'Results/{output_file}')
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

    
    return df


def main():
    '''Primary Function of Script, controls cli control logic, and interprets flags for our use :)
    '''

    # Import Command Arguments
    args=sys.argv[1:]
    try:
        opts, args = getopt.getopt(args,"hl:s:o:p:n:m:",["help","server-id=","outputfile=","location=","pass_threshold="])
    except getopt.GetoptError:
        print(f'INVALID SYNTAX:\n {HELP}')

    #Call Default CLI Values
    num_of_runs = 3
    mode = 'speedtest'
    server = ['Telstra - Melbourne',12491]
    output_file_flag=False

    #Switch Statement - Dirty Because of older python versions
    # TODO When  Python 3.8 reaches EOL, update this to match function
    if len(opts) > 0:
        for opt, arg in opts:
            #Help
            if opt == '-h':
                print(HELP)
                sys.exit()
            #iPerf or Speedtest mode
            elif opt == '-m':
                if 'i' in arg.lower():
                    mode = 'iPerf'
                else:
                    mode = 'Speedtest'
            #Number of Runs
            elif opt == '-n':
                num_of_runs = int(arg)
            #Server IP or ID
            elif opt == '-s':
                server = [f'Custom {mode} Server',arg]
            #Location option (SpeedTest Only)
            elif opt == '-l':
                print(arg)
                #if arg == 'MEL' or 'mel' or 'Melbourne' or 'melbourne':
                if 'mel' in arg.lower():
                    server = ['Telstra - Melbourne',12491]
                elif 'syd' in arg.lower():
                    server = ['Telstra - Sydney',12492]
            #Output File
            elif opt =='-o':
                output_file=f'{arg}.csv'
                output_file_flag=True
            else:
               print(f"ERROR: Unknown argument \n {HELP}")
               sys.exit()
    #Last Minute hack, allows name to be Speedtest OR iPerf AFTER Flag is set    
    if output_file_flag is False:
         output_file = f'{mode.title()}-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    #Push Flags to function
    df = run_test(mode=mode,server=server,num_of_runs=num_of_runs)
    print_results(df_total=df,output_file=output_file)
            

    # Initial test Code.

if __name__ == "__main__":
    main()
