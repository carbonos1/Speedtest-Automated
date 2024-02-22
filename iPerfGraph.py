#!/bin/python
'''Python Script for graphing out iPerf3 results as the product of "pyperftest.py" '''
from datetime import datetime, timedelta
import iperf3
import pandas as pd
import glob
import matplotlib.pyplot as plt


def concat_files(path='./',dfs=[]):
    '''Nabs all the files in the current directory, then combines them together'''
    # Outlines files in current directory
    files = glob.glob(path + "/*.csv")

    for file in files:
         # Read each file as a pandas dataframe
        df = pd.read_csv(file)

        # Group by mode and calculate the mean for sent_mbps and recieved_mbps
        means = df.groupby("mode")[["sent_mbps", "recieved_mbps"]].mean()

        # Reset the index of means to make mode a column
        means = means.reset_index()

        # Add the file name as a column
        means["file"] = file[2:-4]

        # Append the dataframe to the list
        dfs.append(means)

    return pd.concat(dfs, ignore_index=True)
        

def main():
    ''' Primary Function, if left to run normally, this script will '''
    
    iperf_results = concat_files()
    iperf_results.to_excel('iPerfSummary.xlsx')
    upload_results = iperf_results.loc[iperf_results['mode'] == 'Upload']
    download_results = iperf_results.loc[iperf_results['mode'] == 'Download']

    print(f'Download Output: \n ----- \n {download_results}')
    print(f'Upload Ouput: \n ----- \n {upload_results}')
    # Mash the two iperf plots back together again 
    ax = upload_results.plot(x='file',y='recieved_mbps',label='Upload',figsize=(10, 10))
    download_results.plot(x='file',y='recieved_mbps',label='Download',figsize=(10, 10),ax=ax)

    ax.scatter(x=upload_results['file'],y=upload_results['recieved_mbps'])
    ax.scatter(x=download_results['file'],y=download_results['recieved_mbps'])
    

    # Add Data Points to graph
    for i,j in zip(download_results['file'],download_results['recieved_mbps']):
        ax.annotate(str(j),xy=(i,j))

    for i,j in zip(upload_results['file'],upload_results['recieved_mbps']):
        ax.annotate(str(j),xy=(i,j))
    #fig = plt.figure
    ax.grid()
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    plt.show()
    #plt.savefig('iPerfSummary.png')

    # Dummy Code in the 




if __name__ == "__main__":
    main()