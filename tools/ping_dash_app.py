import threading
import subprocess
import time
import datetime
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Global variables to control the pinging thread
pinging = False
ping_thread = None
log_file = "ping_log.csv"

# Function to handle pinging
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
            # Run the ping command
            result = subprocess.run(['ping', '-c', '1', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if result.returncode == 0:
                # Extract latency from the ping result
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
        except Exception as e:
            latency = None
            jitter = None
            packet_loss_count += 1
        
        ping_count += 1
        packet_loss = (packet_loss_count / ping_count) * 100

        with open(log_file, 'a') as f:
            f.write(f"{timestamp},{host},{latency},{jitter},{packet_loss}\n")
        
        time.sleep(interval)

# Read the log file
def read_log_file(log_file):
    df = pd.read_csv(log_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# Calculate jitter and packet loss
def calculate_metrics(df):
    jitter = df['latency'].diff().abs().mean()
    packet_loss = df['latency'].isna().mean() * 100
    return jitter, packet_loss

# Dash app setup
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Ping Results Visualization"),
    dcc.Input(id='host-input', type='text', placeholder='Enter host', debounce=True),
    dcc.Input(id='interval-input', type='number', placeholder='Enter interval (seconds)', debounce=True),
    html.Button('Start', id='start-button', n_clicks=0),
    html.Button('Stop', id='stop-button', n_clicks=0),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,  # in milliseconds
        n_intervals=0
    ),
    dcc.Graph(id='combined-graph'),
    html.Div(id='metrics'),
    dash_table.DataTable(
        id='latency-table',
        columns=[
            {'name': 'Timestamp', 'id': 'timestamp'},
            {'name': 'Host', 'id': 'host'},
            {'name': 'Latency (ms)', 'id': 'latency'},
            {'name': 'Jitter (ms)', 'id': 'jitter'},
            {'name': 'Packet Loss (%)', 'id': 'packet_loss'}
        ],
        data=[]
    ),
    html.Button("Download Data", id="download-button"),
    dcc.Download(id="download-data")
])

@app.callback(
    [Output('combined-graph', 'figure'),
     Output('metrics', 'children'),
     Output('latency-table', 'data')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    df = read_log_file(log_file)
    jitter, packet_loss = calculate_metrics(df)
    
    latency_trace = go.Scatter(
        x=df['timestamp'],
        y=df['latency'],
        mode='lines+markers',
        name='Latency (ms)',
        yaxis='y1'
    )
    
    jitter_trace = go.Scatter(
        x=df['timestamp'],
        y=df['jitter'],
        mode='lines+markers',
        name='Jitter (ms)',
        yaxis='y2'
    )
    
    packet_loss_trace = go.Scatter(
        x=df['timestamp'],
        y=df['packet_loss'],
        mode='lines+markers',
        name='Packet Loss (%)',
        yaxis='y3'
    )
    
    layout = go.Layout(
        title='Ping Metrics Over Time',
        xaxis=dict(title='Time'),
        yaxis=dict(
            title='Latency (ms)',
            side='left'
        ),
        yaxis2=dict(
            title='Jitter (ms)',
            overlaying='y',
            side='right'
        ),
        yaxis3=dict(
            title='Packet Loss (%)',
            overlaying='y',
            side='right',
            position=0.95
        )
    )
    
    figure = go.Figure(data=[latency_trace, jitter_trace, packet_loss_trace], layout=layout)
    
    metrics = [
        html.P(f"Jitter: {jitter:.2f} ms"),
        html.P(f"Packet Loss: {packet_loss:.2f}%")
    ]
    
    table_data = df.to_dict('records')
    
    return figure, metrics, table_data

@app.callback(
    Output('interval-component', 'disabled'),
    [Input('start-button', 'n_clicks'),
     Input('stop-button', 'n_clicks')],
    [State('host-input', 'value'),
     State('interval-input', 'value')]
)
def control_ping(start_clicks, stop_clicks, host, interval):
    global pinging, ping_thread
    
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    
    if 'start-button' in changed_id and host and interval:
        if not pinging:
            pinging = True
            ping_thread = threading.Thread(target=ping, args=(host, float(interval)))
            ping_thread.start()
        return False  # Enable interval updates
    elif 'stop-button' in changed_id:
        if pinging:
            pinging = False
            ping_thread.join()
        return True  # Disable interval updates
    
    return dash.no_update

@app.callback(
    Output("download-data", "data"),
    [Input("download-button", "n_clicks")],
    [State('latency-table', 'data')]
)
def download_data(n_clicks, table_data):
    if n_clicks:
        df = pd.DataFrame(table_data)
        return dcc.send_data_frame(df.to_csv, "ping_data.csv")

if __name__ == '__main__':
    app.run_server(debug=True)
