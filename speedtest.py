#!/bin/python

import os
import json
from datetime import datetime
import sys
import pandas as pd
import numpy as np


def speedtest_prefix():
    '''Simple logic to adjust the speedtest CLI output for usage in differing Operating Systems '''
    if os.name == "nt":
        prefix = ".\speedtest-cli\speedtest.exe"
    elif os.name == "posix":
        prefix =  "./speedtest-cli/speedtest"
    return prefix


def create_dataframe(input_str):
    '''
    Converts the input JSON Dictionary into a Pandas DataFrame.
    Also Determines which values are stored / represented in the output CSV
    Function initially Written by ChatGPT and tweaked by hand :)
     '''
    # Converts input string into JSON object
    data = json.loads(input_str)
    # Retrieve Data Values
    try:
        timestamp = data['timestamp']
    except Exception:
        timestamp = ''
    server_id = data['server']['id']
    server_name = data['server']['name']
    location = data['server']['location']
    ip_address = data['interface']['externalIp']
    download_bandwidth = data['download']['bandwidth'] / 125000
    upload_bandwidth = data['upload']['bandwidth'] / 125000
    latency = data['ping']['latency']
    idle_jitter  = data['ping']['jitter']
    download_jitter  = data['download']['latency']['jitter']
    upload_jitter  = data['upload']['latency']['jitter']
    result_url = data['result']['url']
    # Generate new Dataframe with our New Values
    df = pd.DataFrame({
        'Timestamp': [timestamp],
        'Server Id': [server_id],
        'Server Name': [server_name],
        'Location': [location],
        'Client IP Address': [ip_address],
        'Download Bandwidth (Mbps)': [download_bandwidth],
        'Upload Bandwidth (Mbps)': [upload_bandwidth],
        'Latency' : [latency],
        'Idle Jitter': [idle_jitter],
        'Download Jitter': [download_jitter],
        'Upload Jitter': [upload_jitter],
        'Result URL': [result_url]
    })
    
    return df


def run_speed_test(server_name,server_id,start_time):
    '''Runs Speedtest Results, and outputs the values into a JSON, it will also return the output results as a Pandas Dataframe.'''
    #file_name = f'{server_name}-Speedtest-{start_time}.csv'
    df_total = pd.DataFrame()
    for i in range(6):
        print(f'Running {server_name} Speedtest #{i+1} ')
        df = create_dataframe(os.popen(f'{speedtest_prefix()} -s {server_id} -f json --accept-license').read())
        print(df[['Server Name','Location','Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']])
        df_total = pd.concat([df_total,df])
    return df_total


def main():
    '''Primary Function of the program, controls primary logic when called.'''
    gigacomm_melbourne = ['GigaComm - Melbourne',36100]
    telstra_melbourne = ['Telstra - Melbourne',12491]


    df_gigacomm = run_speed_test(gigacomm_melbourne[0],gigacomm_melbourne[1],0)
    df_telstra = run_speed_test(telstra_melbourne[0],telstra_melbourne[1],0)

    
    df_total = pd.concat([df_gigacomm,df_telstra])
    #Add output CSV

    output_csv = f'Speedtest-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    df_total.to_csv(output_csv)
    print(df_total[['Server Name','Location','Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']])
    print(f'Results Found in {output_csv}')

if __name__ == "__main__":
    main()
