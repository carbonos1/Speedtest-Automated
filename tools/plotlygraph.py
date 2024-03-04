#!/bin/python
'''Python Script for graphing out iPerf3 results as the product of "pyperftest.py"
TOC 3/3/24: Rebuild for Refactor
 '''
from datetime import datetime, timedelta
import pandas as pd
import glob
import plotly.express as px
import plotly.graph_objects as go


def concat_files(path='results/',dfs=[]):
    '''Nabs all the files in the current directory, then combines them together'''
    # Outlines files in current directory
    files = glob.glob(path + "/*.csv")
    for file in files:
         # Read each file as a pandas dataframe
        df = pd.read_csv(file)

        # Group by mode and calculate the mean for Both the Download and upload
        means = df.groupby('Server Name').mean()

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
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Download Bandwidth (Mbps)'],mode='lines+markers',name='Download (in Mbps)'))#,marker_color='blue'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Upload Bandwidth (Mbps)'],mode='lines+markers',name='Upload (in Mbps)'))#,marker_color='red'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Download Jitter'],mode='lines+markers',name='Download jitter (in Ms)'))#,marker_color='green'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Latency'],mode='lines+markers',name=' Idle Latency (in Ms)'))#,marker_color='yellow'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Upload Jitter'],mode='lines+markers',name=' Upload jitter (in Ms)'))#,marker_color='yellow'))
    # Add Data Points to graph
    #for i,j in zip(iperf_results['file'],iperf_results['Download Bandwidth (Mbps)']):
    #fig.add_annotation(x=i,y=j,text=str(round(j,2)),showarrow=False)

    #for i,j in zip(iperf_results['file'],iperf_results['Upload Bandwidth (Mbps)']):
    #fig.add_annotation(x=i,y=j,text=str(round(j,2)),showarrow=False)
    # Set up Table Formatting & add Titles
    title = input('Enter Plot Title:')
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_layout(title=title,plot_bgcolor='white')
    fig.show()

    # Save Figure to Files (scalar and vector)
    fig.write_image(f'results/{title}.png')
    fig.write_image(f'results/{title}.svg')
    




if __name__ == "__main__":
    main()
