#!/usr/bin/env python3
import os
import sys
import threading
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, callback, dash_table, dcc, html, no_update

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.analysis import build_graph, get_results_summary
from wrappers import Speedtest
from wrappers.database import init_database, insert_session

# Background test task state (thread-safe via GIL for simple dict ops)
_test_status = {'running': False, 'result': None, 'error': None}


def _run_speedtest_bg(server_id):
    """Run speedtest in a background thread; stores result in _test_status."""
    global _test_status
    try:
        df = Speedtest().run_test(server_id=int(server_id), num_of_runs=3)
        insert_session(df, 'speedtest')
        avg_dl = df['Download Bandwidth (Mbps)'].mean()
        avg_ul = df['Upload Bandwidth (Mbps)'].mean()
        _test_status['result'] = (avg_dl, avg_ul)
    except Exception as e:
        _test_status['error'] = str(e)
    finally:
        _test_status['running'] = False

PREDEFINED_SERVERS = [
    {'label': 'Telstra - Melbourne (12491)', 'value': '12491'},
    {'label': 'Telstra - Sydney (12492)', 'value': '12492'},
    {'label': 'GigaComm - Melbourne (36100)', 'value': '36100'},
    {'label': 'GigaComm - Sydney (36157)', 'value': '36157'},
    {'label': 'Custom Server ID', 'value': 'custom'},
]

app = Dash(__name__)

app.layout = html.Div([
    html.H1('Throughput Performance Dashboard',
            style={'marginBottom': '30px', 'color': '#1a1a1a', 'fontSize': '2.5rem'}),

    html.Div([
        html.Div([
            html.Label('Select Speedtest Server:',
                      style={'display': 'block', 'marginBottom': '8px', 'fontWeight': '500', 'color': '#333333'}),
            dcc.Dropdown(
                id='server-dropdown',
                options=PREDEFINED_SERVERS,
                value='12491',
                clearable=False,
                style={'marginBottom': '10px'}
            ),
            dcc.Input(
                id='custom-server-input',
                type='text',
                placeholder='Enter custom server ID',
                style={
                    'width': '100%',
                    'padding': '10px',
                    'border': '1px solid #d0d0d0',
                    'borderRadius': '4px',
                    'fontSize': '14px',
                    'display': 'none'
                }
            ),
        ], style={'flex': '1', 'marginRight': '20px'}),

        html.Div([
            dcc.Loading(
                id='loading-button',
                type='circle',
                children=[
                    html.Button('Run Speed Test', id='run-test-btn', n_clicks=0,
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
                               })
                ]
            ),
            dcc.Checklist(
                id='autorefresh-toggle',
                options=[{'label': ' Enable Auto Refresh (60s)', 'value': 'enabled'}],
                value=[],
                style={'color': '#333333', 'fontSize': '14px'}
            ),
        ], style={'flex': '0 0 250px'}),
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
        id='refresh-interval',
        interval=60000,
        disabled=True,
        n_intervals=0
    ),

    dcc.Interval(
        id='test-poll-interval',
        interval=2000,
        disabled=True,
        n_intervals=0
    ),

    dcc.Store(id='test-trigger', data=0),

    dcc.Download(id='download-data'),

    dcc.Loading(
        id='loading-graph',
        type='default',
        children=[
            dcc.Graph(id='performance-graph', style={'height': '800px'})
        ]
    ),

    html.Div(id='progress-message', style={
        'marginTop': '20px',
        'padding': '15px',
        'backgroundColor': '#e3f2fd',
        'borderRadius': '4px',
        'color': '#1976d2',
        'fontSize': '14px',
        'fontWeight': '500',
        'display': 'none'
    }),

    html.Div([
        html.H2('Throughput Performance Table',
                style={'margin': 0, 'color': '#1a1a1a'}),
        html.Button('Download CSV', id='download-btn', n_clicks=0,
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
        id='results-table',
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
    )
], style={
    'maxWidth': '1400px',
    'margin': '0 auto',
    'padding': '40px',
    'backgroundColor': '#ffffff',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
})


@callback(
    Output('custom-server-input', 'style'),
    Input('server-dropdown', 'value')
)
def toggle_custom_input(selected_value):
    if selected_value == 'custom':
        return {
            'width': '100%',
            'padding': '10px',
            'border': '1px solid #d0d0d0',
            'borderRadius': '4px',
            'fontSize': '14px',
            'display': 'block'
        }
    return {
        'width': '100%',
        'padding': '10px',
        'border': '1px solid #d0d0d0',
        'borderRadius': '4px',
        'fontSize': '14px',
        'display': 'none'
    }


@callback(
    [Output('performance-graph', 'figure'),
     Output('results-table', 'data'),
     Output('results-table', 'columns')],
    [Input('refresh-interval', 'n_intervals'),
     Input('test-trigger', 'data')],
    prevent_initial_call=False
)
def update_dashboard(n_intervals, test_trigger):
    results = get_results_summary()

    if results.empty:
        fig = go.Figure()
        fig.update_layout(
            title=f'No data available (generated {datetime.now()})',
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#333333')
        )
        return fig, [], []

    fig = build_graph(results)

    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='#333333', size=12),
        title_font=dict(size=18, color='#1a1a1a'),
        xaxis=dict(
            showgrid=True,
            gridcolor='#e8e8e8',
            gridwidth=1,
            showline=True,
            linewidth=2,
            linecolor='#333333',
            tickfont=dict(size=11, color='#333333')
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e8e8e8',
            gridwidth=1,
            showline=True,
            linewidth=2,
            linecolor='#333333',
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

    for trace in fig.data:
        if trace.line.width is None or trace.line.width < 2:
            trace.line.width = 2.5
        if trace.marker.size is None or trace.marker.size < 6:
            trace.marker.size = 6

    # Safely handle NaN values so we generate valid JSON without 'NaN' literals
    table_data = []
    for row in results.to_dict('records'):
        clean_row = {}
        for k, v in row.items():
            if pd.isna(v) or v is pd.NA:
                clean_row[k] = None
            else:
                clean_row[k] = v
        table_data.append(clean_row)

    table_columns = [{'name': col, 'id': col} for col in results.columns]

    return fig, table_data, table_columns


@callback(
    Output('refresh-interval', 'disabled'),
    Input('autorefresh-toggle', 'value')
)
def toggle_autorefresh(value):
    return 'enabled' not in value


@callback(
    [Output('progress-message', 'children'),
     Output('progress-message', 'style'),
     Output('run-test-btn', 'disabled'),
     Output('test-poll-interval', 'disabled')],
    Input('run-test-btn', 'n_clicks'),
    [State('server-dropdown', 'value'),
     State('custom-server-input', 'value')],
    prevent_initial_call=True
)
def start_speedtest(n_clicks, server_selection, custom_server_id):
    """Start a speedtest in a background thread; show 'Running...' immediately."""
    global _test_status
    if n_clicks > 0:
        server_id = custom_server_id if server_selection == 'custom' else server_selection

        if not server_id:
            return 'Please enter a valid server ID', {
                'marginTop': '20px', 'padding': '15px',
                'backgroundColor': '#ffebee', 'borderRadius': '4px',
                'color': '#c62828', 'fontSize': '14px', 'fontWeight': '500',
                'display': 'block'
            }, False, True

        _test_status = {'running': True, 'result': None, 'error': None}
        thread = threading.Thread(target=_run_speedtest_bg, args=(server_id,))
        thread.daemon = True
        thread.start()

        return 'Running speedtest (3 runs)... this may take a minute.', {
            'marginTop': '20px', 'padding': '15px',
            'backgroundColor': '#e3f2fd', 'borderRadius': '4px',
            'color': '#1976d2', 'fontSize': '14px', 'fontWeight': '500',
            'display': 'block'
        }, True, False

    return '', {'display': 'none'}, False, True


@callback(
    [Output('progress-message', 'children', allow_duplicate=True),
     Output('progress-message', 'style', allow_duplicate=True),
     Output('test-trigger', 'data'),
     Output('run-test-btn', 'disabled', allow_duplicate=True),
     Output('test-poll-interval', 'disabled', allow_duplicate=True)],
    Input('test-poll-interval', 'n_intervals'),
    [State('test-trigger', 'data')],
    prevent_initial_call=True
)
def poll_speedtest(n_intervals, current_trigger):
    """Poll for background speedtest completion and update the dashboard."""
    global _test_status
    if _test_status['running']:
        return no_update, no_update, no_update, no_update, no_update

    trigger_val = current_trigger if current_trigger is not None else 0

    if _test_status['error']:
        err = _test_status['error']
        _test_status['error'] = None
        return f'Error running speedtest: {err}', {
            'marginTop': '20px', 'padding': '15px',
            'backgroundColor': '#ffebee', 'borderRadius': '4px',
            'color': '#c62828', 'fontSize': '14px', 'fontWeight': '500',
            'display': 'block'
        }, trigger_val, False, True

    if _test_status['result']:
        avg_dl, avg_ul = _test_status['result']
        _test_status['result'] = None
        return (f'Speedtest completed! Average of 3 runs - '
                f'Download: {avg_dl:.2f} Mbps, Upload: {avg_ul:.2f} Mbps'), {
            'marginTop': '20px', 'padding': '15px',
            'backgroundColor': '#e8f5e9', 'borderRadius': '4px',
            'color': '#2e7d32', 'fontSize': '14px', 'fontWeight': '500',
            'display': 'block'
        }, trigger_val + 1, False, True

    return no_update, no_update, no_update, False, True


@callback(
    Output('download-data', 'data'),
    Input('download-btn', 'n_clicks'),
    prevent_initial_call=True
)
def download_csv(n_clicks):
    df = get_results_summary()
    if df.empty:
        return None
    csv_string = df.to_csv(index=False)
    filename = f'speedtest_results_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    return dict(content=csv_string, filename=filename)


if __name__ == '__main__':
    init_database()
    app.run(debug=True, port=8050, host='0.0.0.0')
