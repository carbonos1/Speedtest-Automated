'''Wrapper for Speedtest Executable.
This modules allows us to generate a speedtest.net result, and convert it into pandas dataframe'''
import os
import json
import pandas as pd

class Speedtest:
    """ Main Class of File,
    Contains the functions used to convert the Speedtest.net Binary into Pandas Dataframes so the code is a bit easier to play with
    """
    def __init__(self) -> None:
        ''' Set Pre-Defined servers for us to point to. TODO see if we can get these values automagically'''
        GIGACOMM_MELBOURNE = ['GigaComm - Melbourne',36100]
        TELSTRA_MELBOURNE = ['Telstra - Melbourne',12491]
        GIGACOMM_SYDNEY = ['GigaComm - Sydney',36157]
        TELSTRA_SYDNEY = ['Telstra - Sydney',12492]
    def speedtest_prefix(self):
        '''Simple logic to adjust the speedtest CLI output for usage in differing Operating Systems.
        TODO: this is a little janky, see if we can do this a bit better.
        TODO: re-factor for new Directory Layout
        '''
        if os.name == "nt":
            prefix = ".\\bin\speedtest.exe"
        elif os.name == "posix":
            prefix =  "bin/speedtest"
        return prefix
    def run_test(self,server_name = 'Server:',server_id = 14670,num_of_runs=6):
        '''Runs Speedtest Results, and outputs the values into a JSON, it will also return the output results as a Pandas Dataframe.
        server_name = Name of the Server Passed'''
        df_total = pd.DataFrame()
        for i in range(num_of_runs):
            print(f'Running {server_name} Speedtest #{i+1} ')
            df = self.create_dataframe(os.popen(f'{self.speedtest_prefix()} -s {server_id} -f json --accept-license').read())
            print(df[['Server Name','Location','Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']])
            df_total = pd.concat([df_total,df],ignore_index=True)
        return df_total
    def create_dataframe(self,input_str):
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
            'Mode': 'SpeedTest',
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
