'''DocString'''
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from wrappers.database import init_database, get_all_results, insert_speedtest
from wrappers import Speedtest

RENAME_MAP = {
    'download_mbps': 'Download Bandwidth (Mbps)',
    'upload_mbps': 'Upload Bandwidth (Mbps)',
    'download_jitter': 'Download Jitter',
    'upload_jitter': 'Upload Jitter',
    'latency': 'Latency',
}

def get_results_summary():
    '''Get summary results from the SQLite database grouped by file/timestamp'''
    speedtest, iperf = get_all_results()
    
    if not speedtest.empty:
        speedtest = speedtest.rename(columns=RENAME_MAP)
        speedtest['file'] = pd.to_datetime(speedtest['timestamp']).dt.strftime('%Y-%m-%d_%H-%M-%S')
        speedtest_means = speedtest.groupby('file')[['Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']].mean().reset_index()
        speedtest_means['Server Name'] = speedtest.groupby('file')['server_name'].first()
        try:
            jitter_cols = speedtest.groupby('file')[['Download Jitter','Latency','Upload Jitter']].mean()
            speedtest_means = speedtest_means.merge(jitter_cols, left_on='file', right_index=True)
        except KeyError:
            pass
    else:
        speedtest_means = pd.DataFrame()
    
    if not iperf.empty:
        iperf = iperf.rename(columns=RENAME_MAP)
        iperf['file'] = pd.to_datetime(iperf['test_datetime']).dt.strftime('%Y-%m-%d_%H-%M-%S')
        iperf_means = iperf.groupby('file')[['Download Bandwidth (Mbps)','Upload Bandwidth (Mbps)']].mean().reset_index()
        iperf_means['Server Name'] = iperf.groupby('file')['server_name'].first()
    else:
        iperf_means = pd.DataFrame()
    
    combined = pd.concat([speedtest_means, iperf_means], ignore_index=True)
    return combined.sort_values('file').reset_index(drop=True) if not combined.empty else combined
def build_graph(iperf_results):
    ''' Builds the Graph for us :)'''

    # Mash the two iperf plots back together again 
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=iperf_results['file'],
        y=iperf_results['Download Bandwidth (Mbps)'],
        mode='lines+markers',
        name='Download (in Mbps)',
        marker_color='deepskyblue'
        ))
    fig.add_trace(go.Scatter(x=iperf_results['file'],y=iperf_results['Upload Bandwidth (Mbps)'],mode='lines+markers',name='Upload (in Mbps)',marker_color='orangered'))
    try:
        fig.add_trace(go.Scatter(
            x=iperf_results['file'],
            y=iperf_results['Download Jitter'],
            mode='lines+markers',
            name='Download jitter (in Ms)',
            visible='legendonly',
            marker_color='limegreen'))
        fig.add_trace(go.Scatter(x=iperf_results['file'],
            y=iperf_results['Latency'],
            mode='lines+markers',
            name=' Idle Latency (in Ms)',
            visible='legendonly',
            marker_color='salmon'
            ))
        fig.add_trace(go.Scatter(x=iperf_results['file'],
            y=iperf_results['Upload Jitter'],
            mode='lines+markers',
            name=' Upload jitter (in Ms)',
            visible='legendonly',
            marker_color='magenta'
            ))
    except KeyError:
        pass # If we don't have these lines, why draw them? It's better to Ignore TODO Come up with a more elegant solution here.
    except Exception as exception:
        print(exception)
    title = f'Speedtest performance results (generated {datetime.now()})'
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_layout(title=title,plot_bgcolor='white',height=800)
    
    return fig

def main():
    init_database()
    iperf_results = get_results_summary()
    st.set_page_config(layout="wide")
    st.header('Throughput Performance Graph')

    col1, col2, col3 = st.columns([8,1,1])
    with col2:
        if st.button('Run Speed Test'):
            df = Speedtest().run_test(num_of_runs=3)
            insert_speedtest(df)
            st.rerun()
    with col3:
        if st.checkbox('Enable Auto Refresh'):
            st_autorefresh(interval=60000, key='some_key')

    st.plotly_chart(build_graph(iperf_results),use_container_width=True,height=800)
    st.header('Throughput Performance Table')
    st.dataframe(iperf_results,use_container_width=True)



if __name__ == "__main__":
    main()