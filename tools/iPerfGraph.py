#!/usr/bin/env python3
'''Python Script for graphing out iPerf3 results as the product of "pyperftest.py"
TOC 3/3/24: Rebuild for Refactor
 '''
from datetime import datetime, timedelta
import pandas as pd
import glob
import matplotlib.pyplot as plt


def concat_files(path='results/',dfs=[]):
    '''Nabs all the files in the current directory, then combines them together'''
    # Outlines files in current directory
    files = glob.glob(path + "/*.csv")
    for file in files:
         # Read each file as a pandas dataframe
        df = pd.read_csv(file)

        # Group by mode and calculate the mean for Both the Download and upload
        means = df.groupby('Server Name')[['Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']].mean()

        # Reset the index of means to make mode a column
        means = means.reset_index()

        # Add the file name as a column
        means["file"] = file[8:-4]

        # Append the dataframe to the list
        dfs.append(means)

    return pd.concat(dfs, ignore_index=True).sort_values('file').reset_index().drop(columns='index')
def main():
    ''' Builds the Graph for us :)'''
    
    iperf_results = concat_files()
    iperf_results.to_excel('results/iPerfSummary.xlsx')
    print()


    print(f'\n----------\nAverages Output:\n----------\n {iperf_results}')
    # Mash the two iperf plots back together again 
    ax = iperf_results.plot(x='file',y='Download Bandwidth (Mbps)',label='Download (in Mbps)',figsize=(10, 5))
    iperf_results.plot(x='file',y='Upload Bandwidth (Mbps)',label='Upload (in Mbps)',ax=ax)
    ax.scatter(x=iperf_results['file'],y=iperf_results['Download Bandwidth (Mbps)'])
    ax.scatter(x=iperf_results['file'],y=iperf_results['Upload Bandwidth (Mbps)'])
    
    # Add Data Points to graph
    for i,j in zip(iperf_results['file'],iperf_results['Download Bandwidth (Mbps)']):
        ax.annotate(str(round(j,2)),xy=(i,j))

    for i,j in zip(iperf_results['file'],iperf_results['Upload Bandwidth (Mbps)']):
        ax.annotate(str(round(j,2)),xy=(i,j))
    #fig = plt.figure
    
    # Set up Table Formatting & add Titles
    title = input('Enter Plot Title:')
    ax.grid()
    plt.setp(ax.get_xticklabels(), rotation=10, ha="right")
    plt.title(title)

    # Save Figure to Files (scalar and vector)
    plt.savefig(f'results/{title}.png')
    plt.savefig(f'results/{title}.svg')
    #plt.show()
   



if __name__ == "__main__":
    main()