#!/bin/python
'''simple module to batch run iPerf tests'''
# Import the required modules
from datetime import datetime
import iperf3
import pandas as pd
import sys

# Define a function that takes the iperf3 server address, the test duration, and the reverse mode as parameters
def iperf_test(server, duration, reverse):
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
        # Filter the dataframe to return only the sum_sent and sum_received bits_per_second columns
        df = df.filter(['sent_bps','received_bps'])
        # Convert the bits_per_second to megabits_per_second and round to two decimals
        df['sent_mbps'] = round(df['sent_bps'] / 1e6, 2)
        df['recieved_mbps'] = round(df['received_bps'] / 1e6, 2)
        # Drop the bits_per_second columns
        df = df.drop(['sent_bps', 'received_bps'], axis=1)
        # Return the filtered dataframe
        return df

def main():
    '''Primary Function, runs a batch of iperf tests at a designated host'''
    dfs = []
    for server in sys.argv[1:]:
      # Loop to add additional testing
        print(f'Testing {server}')
        for i in range(3):
            print(f'Test {i+1}')
            # Run a 10-second test in forward mode (client as sender)
            df_forward = iperf_test(server, 10, False)
            # Add a column to indicate the test mode and the server address
            df_forward['mode'] = 'Upload'
            df_forward['server'] = server

            print (df_forward)
            # Append the dataframe to the list of dataframes
            dfs.append(df_forward)
            # Run a 10-second test in reverse mode (client as receiver)
            df_reverse = iperf_test(server, 10, True)
            # Add a column to indicate the test mode and the server address
            df_reverse['mode'] = 'Download'
            df_reverse['server'] = server

            print(df_reverse)
            # Append the dataframe to the list of dataframes
            dfs.append(df_reverse)

    # Concatenate all the dataframes into one final dataframe
    df_final = pd.concat(dfs, ignore_index=True)

    # Print the final dataframe
    print('-------\nOutput\n-------')
    print(df_final)
    output_csv = f'iPerf3-{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    df_final.to_csv(output_csv)
    print(f'Results Found in {output_csv}')

    #Find the average of all iPer tests and print them to screen
    print('-------\nAverage\n-------')
    df_average = df_final.groupby("mode")[["sent_mbps", "recieved_mbps"]].mean()
    df_average = df_average.reset_index()
    print(df_average)


if __name__ == "__main__":
    main()
