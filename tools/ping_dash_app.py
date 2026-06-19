import datetime
import os
import subprocess
import threading
import time

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dash_table, dcc, html

# Global variables to control the pinging thread
pinging = False
ping_thread = None
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'ping_log.csv')


def ping(host, interval):
    global pinging
    with open(log_file, 'w') as f:
        f.write("timestamp,host,latency,jitter,packet_loss\n")

    previous_latency = None
    packet_loss_count = 0
    ping_count = 0

    while pinging:
        timestamp = datetime.datetime.now().isoformat()
        try:
            result = subprocess.run(
                ['ping', '-c', '1', host],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout
                latency_line = output.split('\n')[1]
                latency = latency_line.split('time=')[1].split(' ')[0]
                latency = float(latency)
                if previous_latency is not None:
                    jitter = abs(latency - previous_latency)
                else:
                    jitter = 0
                previous_latency = latency
            else:
                latency = None
                jitter = None
                packet_loss_count += 1
        except Exception:
            latency = None
            jitter = None
            packet_loss_count += 1

        ping_count += 1
        packet_loss = (packet_loss_count / ping_count) * 100

        with open(log_file, 'a') as f:
            f.write(f"{timestamp},{host},{latency},{jitter},{packet_loss}\n")

        time.sleep(interval)


def read_log_file(log_file):
    if not os.path.exists(log_file):
        return pd.DataFrame(columns=['timestamp', 'host', 'latency', 'jitter', 'packet_loss'])
    df = pd.read_csv(log_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


def calculate_metrics(df):
    if df.empty:
        return 0.0, 0.0
    jitter = df['latency'].diff().abs().mean()
    packet_loss = df['latency'].isna().mean() * 100
    return jitter, packet_loss


app = Dash(__name__)

app.layout = html.Div([
    html.H1('Ping Results Visualization',
            style={'marginBottom': '30px', 'color': '#1a1a1a', 'fontSize': '2.5rem'}),

    html.Div([
        html.Div([
            html.Label('Host:',
                      style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500', 'color': '#333333'}),
            dcc.Input(
                id='host-input', type='text', placeholder='Enter host',
                style={
                    'width': '100%',
                    'padding': '10px',
                    'border': '1px solid #d0d0d0',
                    'borderRadius': '4px',
                    'fontSize': '14px'
                }
            ),
        ], style={'flex': '1', 'marginRight': '20px'}),

        html.Div([
            html.Label('Interval (seconds):',
                      style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500', 'color': '#333333'}),
            dcc.Input(
                id='interval-input', type='number', placeholder='Interval',
                style={
                    'width': '100%',
                    'padding': '10px',
                    'border': '1px solid #d0d0d0',
                    'borderRadius': '4px',
                    'fontSize': '14px'
                }
            ),
        ], style={'flex': '1', 'marginRight': '20px'}),

        html.Div([
            html.Button('Start', id='start-button', n_clicks=0,
                       style={
                           'padding': '12px 24px',
                           'backgroundColor': '#0066cc',
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '4px',
                           'cursor': 'pointer',
                           'fontSize': '14px',
                           'fontWeight': '500',
                           'marginBottom': '10px',
                           'width': '100%'
                       }),
            html.Button('Stop', id='stop-button', n_clicks=0,
                       style={
                           'padding': '12px 24px',
                           'backgroundColor': '#c62828',
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '4px',
                           'cursor': 'pointer',
                           'fontSize': '14px',
                           'fontWeight': '500',
                           'width': '100%'
                       }),
        ], style={'flex': '0 0 150px'}),
    ], style={
        'marginBottom': '30px',
        'padding': '20px',
        'backgroundColor': '#f5f5f5',
        'borderRadius': '8px',
        'border': '1px solid #e0e0e0',
        'display': 'flex',
        'alignItems': 'flex-end'
    }),

    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0,
        disabled=True
    ),

    dcc.Graph(id='combined-graph', style={'height': '600px'}),

    html.Div(id='metrics', style={
        'marginTop': '20px',
        'padding': '15px',
        'backgroundColor': '#e3f2fd',
        'borderRadius': '4px',
        'color': '#1976d2',
        'fontSize': '14px',
        'fontWeight': '500',
    }),

    html.Div([
        html.H2('Ping Log',
                style={'margin': 0, 'color': '#1a1a1a'}),
        html.Button('Download Data', id='download-button', n_clicks=0,
                   style={
                       'padding': '8px 16px',
                       'backgroundColor': '#0066cc',
                       'color': 'white',
                       'border': 'none',
                       'borderRadius': '4px',
                       'cursor': 'pointer',
                       'fontSize': '14px',
                       'fontWeight': '500'
                   }),
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginTop': '50px', 'marginBottom': '20px'}),

    dash_table.DataTable(
        id='latency-table',
        columns=[
            {'name': 'Timestamp', 'id': 'timestamp'},
            {'name': 'Host', 'id': 'host'},
            {'name': 'Latency (ms)', 'id': 'latency'},
            {'name': 'Jitter (ms)', 'id': 'jitter'},
            {'name': 'Packet Loss (%)', 'id': 'packet_loss'}
        ],
        data=[],
        page_size=20,
        sort_action='native',
        filter_action='native',
        style_table={
            'overflowX': 'auto',
            'border': '1px solid #e0e0e0',
            'borderRadius': '8px'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'backgroundColor': 'white',
            'color': '#333333',
            'fontSize': '14px',
            'borderBottom': '1px solid #e8e8e8'
        },
        style_header={
            'backgroundColor': '#f0f0f0',
            'fontWeight': '600',
            'color': '#1a1a1a',
            'borderBottom': '2px solid #d0d0d0',
            'fontSize': '14px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#fafafa'
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#e3f2fd',
                'color': '#1a1a1a'
            }
        ]
    ),

    dcc.Download(id="download-data")
], style={
    'maxWidth': '1400px',
    'margin': '0 auto',
    'padding': '40px',
    'backgroundColor': '#ffffff',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
})


@ app.callback(
    [Output('combined-graph', 'figure'),
     Output('metrics', 'children'),
     Output('latency-table', 'data')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    df = read_log_file(log_file)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title='No data yet',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#333333')
        )
        return fig, [html.P("Waiting for data...")], []

    jitter, packet_loss = calculate_metrics(df)

    latency_trace = go.Scatter(
        x=df['timestamp'],
        y=df['latency'],
        mode='lines+markers',
        name='Latency (ms)',
        yaxis='y1',
        line=dict(width=2.5),
        marker=dict(size=6)
    )

    jitter_trace = go.Scatter(
        x=df['timestamp'],
        y=df['jitter'],
        mode='lines+markers',
        name='Jitter (ms)',
        yaxis='y2',
        line=dict(width=2.5),
        marker=dict(size=6)
    )

    packet_loss_trace = go.Scatter(
        x=df['timestamp'],
        y=df['packet_loss'],
        mode='lines+markers',
        name='Packet Loss (%)',
        yaxis='y3',
        line=dict(width=2.5),
        marker=dict(size=6)
    )

    layout = go.Layout(
        title=dict(text='Ping Metrics Over Time', font=dict(size=18, color='#1a1a1a')),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333', size=12),
        xaxis=dict(
            title='Time',
            showgrid=True,
            gridcolor='#e8e8e8',
            gridwidth=1,
            showline=True,
            linewidth=2,
            linecolor='#333333',
            tickfont=dict(size=11, color='#333333')
        ),
        yaxis=dict(
            title='Latency (ms)',
            side='left',
            showgrid=True,
            gridcolor='#e8e8e8',
            gridwidth=1,
            showline=True,
            linewidth=2,
            linecolor='#333333',
            tickfont=dict(size=11, color='#333333')
        ),
        yaxis2=dict(
            title='Jitter (ms)',
            overlaying='y',
            side='right',
            showgrid=False,
            tickfont=dict(size=11, color='#333333')
        ),
        yaxis3=dict(
            title='Packet Loss (%)',
            overlaying='y',
            side='right',
            position=0.95,
            showgrid=False,
            tickfont=dict(size=11, color='#333333')
        ),
        legend=dict(
            bgcolor='rgba(255, 255, 255, 0.9)',
            bordercolor='#e0e0e0',
            borderwidth=1,
            font=dict(size=12, color='#333333')
        ),
        margin=dict(l=60, r=40, t=60, b=60)
    )

    figure = go.Figure(data=[latency_trace, jitter_trace, packet_loss_trace], layout=layout)

    metrics = [
        html.Span(f"Jitter: {jitter:.2f} ms", style={'marginRight': '20px'}),
        html.Span(f"Packet Loss: {packet_loss:.2f}%")
    ]

    table_data = df.to_dict('records')

    return figure, metrics, table_data


@ app.callback(
    Output('interval-component', 'disabled'),
    [Input('start-button', 'n_clicks'),
     Input('stop-button', 'n_clicks')],
    [State('host-input', 'value'),
     State('interval-input', 'value')]
)
def control_ping(start_clicks, stop_clicks, host, interval):
    global pinging, ping_thread

    changed_id = [p['prop_id'] for p in ctx.triggered][0]

    if 'start-button' in changed_id and host and interval:
        if not pinging:
            pinging = True
            ping_thread = threading.Thread(target=ping, args=(host, float(interval)))
            ping_thread.start()
        return False
    elif 'stop-button' in changed_id:
        if pinging:
            pinging = False
            ping_thread.join()
        return True

    return True


@ app.callback(
    Output("download-data", "data"),
    [Input("download-button", "n_clicks")],
    [State('latency-table', 'data')],
    prevent_initial_call=True
)
def download_data(n_clicks, table_data):
    if n_clicks and table_data:
        df = pd.DataFrame(table_data)
        return dict(content=df.to_csv(index=False), filename="ping_data.csv")
    return None


if __name__ == '__main__':
    app.run(debug=True, port=8051)
