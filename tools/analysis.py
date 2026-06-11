import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from wrappers.database import get_all_results

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
        speedtest_means['Server Name'] = speedtest.groupby('file')['server_name'].first().values
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
        iperf_means['Server Name'] = iperf.groupby('file')['server_name'].first().values
    else:
        iperf_means = pd.DataFrame()
    
    combined = pd.concat([speedtest_means, iperf_means], ignore_index=True)
    return combined.sort_values('file').reset_index(drop=True) if not combined.empty else combined

def build_graph(iperf_results):
    ''' Builds the graph for us :)'''
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
        pass
    except Exception as exception:
        print(exception)
    title = f'Speedtest performance results (generated {datetime.now()})'
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black',gridcolor='lightgrey')
    fig.update_layout(title=title,plot_bgcolor='white',height=800)
    
    return fig
