import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from wrappers.database import get_all_session_results

RENAME_MAP = {
    'download_mbps': 'Download Bandwidth (Mbps)',
    'upload_mbps': 'Upload Bandwidth (Mbps)',
    'download_jitter': 'Download Jitter',
    'upload_jitter': 'Upload Jitter',
    'latency': 'Latency',
}

def get_results_summary():
    '''Get session-level results from the SQLite database.

    Returns one row per test session (pre-computed averages from
    test_sessions), ready for graphing and tabular display. Replaces the
    legacy get_all_results() + groupby-averaging path.
    '''
    sessions = get_all_session_results()
    if sessions.empty:
        return sessions
    # get_all_session_results already renames columns and adds 'file'/'datetime'
    return sessions

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
