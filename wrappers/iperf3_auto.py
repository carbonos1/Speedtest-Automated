'''simple module to batch run iPerf tests using the iperf3'''
# Import the required modules
import iperf3 # This Library is doing the leg work ere
import pandas as pd
from datetime import datetime

class Iperf3Auto:
    """ Main Class of File
    the Goal of this class is to:
     -  emulate how our speedtest class is making tests, and mimic that using iperf3
     - return a pandas dataframe that we can use to graph data"""
    def __init__(self) -> None:
        pass
    def iperf_test(self,server, duration, reverse):
        ''' Pushes Through the iPerfTests using iPerf'''
        # Create an iperf3 client object
        client = iperf3.Client()
        # Set the server address, the test duration, and the reverse mode
        client.server_hostname = server
        client.duration = duration
        client.reverse = reverse
        # Run the test and get the result object
        result = client.run()
        # Check if the test was successful
        if result.error:
            print(f'Error: {result.error}')
        else:
            # Create a pandas dataframe with the result attributes
            df = pd.DataFrame([result.__dict__])
            # Filter the dataframe for desired Columns only, there's a lot of data in here
            df = df.filter(['timesecs','num_streams','sent_bps','received_bps'])
            # Convert the bits_per_second to megabits_per_second and round to two decimals
            df['datetime'] = datetime.fromtimestamp(int(df['timesecs']))
            df['sent_mbps'] = round(df['sent_bps'] / 1e6, 2)
            df['recieved_mbps'] = round(df['received_bps'] / 1e6, 2)
            # Drop the bits_per_second columns
            df = df.drop(['sent_bps', 'received_bps','timesecs'], axis=1)
            # Return the filtered dataframe
            return df
    def run_test(self,server,num_of_runs=3):
        '''Basic Control Logic to get Mimic that speedtest.net behaviour, requires server to run'''
        dfs = []
        for i in range(num_of_runs):
            print(f'Running {server}: iPerf {i + 1}')

            # Mimic a Speedtest.net Download Test, then append the Download type to it.
            df_download = self.iperf_test(server,10,True)
            
            # Mimic a Speedtest.net Upload Test, then append Upload to the result
            df_upload = self.iperf_test(server,10,False)

            # Combine both DataFrames into a combined one with the relevant data we need. 
            #Note we use 'recieved_mbps' to measure traffic that has actually gone across the link
            df_combo = pd.DataFrame()
            df_combo.loc[0,'Mode'] = 'iPerf3'
            df_combo.loc[0,'Server Name'] = f'{server}'
            df_combo['datetime'] = df_upload['datetime']
            df_combo['Download Bandwidth (Mbps)'] = df_download['recieved_mbps']
            df_combo['Upload Bandwidth (Mbps)'] = df_upload['recieved_mbps']
            df_combo['Number of Streams (DL)'] = df_download['num_streams']
            df_combo['Number of Streams (UL)'] = df_upload['num_streams']

            
            print(df_combo[['Server Name','Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']])

            dfs.append(df_combo)
        # Concat ALL Dataframes and return to 
        return pd.concat(dfs,ignore_index=True)
            





            