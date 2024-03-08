'''DocString'''
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import glob
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

def concat_files(path='results/',dfs=[]):
    '''Nabs all the files in the current directory, then combines them together'''
    # Outlines files in current directory
    files = glob.glob(path + "/*.csv")
    for file in files:
         # Read each file as a pandas dataframe
        df = pd.read_csv(file)

        # Group by mode and calculate the mean for Both the Download and upload
        means = df.groupby('Server Name')[['Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)','Download Jitter','Latency','Upload Jitter']].mean()

        # Reset the index of means to make mode a column
        means = means.reset_index()

        # Add the file name as a column
        means["file"] = file[8:-4]

        # Append the dataframe to the list
        dfs.append(means)

    return pd.concat(dfs, ignore_index=True).sort_values('file').reset_index().drop(columns='index')
def build_graph(iperf_results):
    ''' Builds the Graph for us :)'''

    # Mash the two iperf plots back together again 
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Download Bandwidth (Mbps)'],mode='lines+markers',name='Download (in Mbps)',marker_color='deepskyblue'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Upload Bandwidth (Mbps)'],mode='lines+markers',name='Upload (in Mbps)',marker_color='orangered'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Download Jitter'],mode='lines+markers',name='Download jitter (in Ms)',visible='legendonly',marker_color='limegreen'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Latency'],mode='lines+markers',name=' Idle Latency (in Ms)',visible='legendonly',marker_color='salmon'))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Upload Jitter'],mode='lines+markers',name=' Upload jitter (in Ms)',visible='legendonly',marker_color='magenta'))
    # Add Data Points to graph
    #for i,j in zip(iperf_results['file'],iperf_results['Download Bandwidth (Mbps)']):
    #fig.add_annotation(x=i,y=j,text=str(round(j,2)),showarrow=False)

    #for i,j in zip(iperf_results['file'],iperf_results['Upload Bandwidth (Mbps)']):
    #fig.add_annotation(x=i,y=j,text=str(round(j,2)),showarrow=False)
    # Set up Table Formatting & add Titles
    title = f'Speedtest performance results (generated {datetime.now()})'
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_layout(title=title,plot_bgcolor='white',height=800)
    
    return fig

def main():

    iperf_results = concat_files()
    iperf_results.to_excel('results/iPerfSummary.xlsx')
    #print(f'\n----------\nAverages Output:\n----------\n {iperf_results}')
    # Set page to wide mode
    st.set_page_config(layout="wide")
    # Set up autorefresh to rerun the app every 60 seconds
    st_autorefresh(interval=60000, key='some_key')  
    # Page Formatting
    # Build Performance Graph and output in streamlit
    st.header('Throughput Performance Graph')
    st.plotly_chart(build_graph(iperf_results),use_container_width=True,height=800)
    # Output Table and place in Streamlit.
    st.header('Throughput Performance Table')
    st.dataframe(iperf_results,use_container_width=True)



if __name__ == "__main__":
    main()