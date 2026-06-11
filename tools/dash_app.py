#!/usr/bin/env python3
import os
import sys
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback, ctx

# Ensure the project root is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrappers.database import init_database, insert_speedtest
from wrappers import Speedtest
from tools.analyse_results import get_results_summary, build_graph

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
    
    dcc.Store(id='test-trigger', data=0),
    
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
    
    html.H2('Throughput Performance Table', 
            style={'marginTop': '50px', 'marginBottom': '20px', 'color': '#1a1a1a'}),
    
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
     Output('test-trigger', 'data'),
     Output('run-test-btn', 'disabled')],
    Input('run-test-btn', 'n_clicks'),
    [State('server-dropdown', 'value'),
     State('custom-server-input', 'value'),
     State('test-trigger', 'data')],
    prevent_initial_call=True
)
def run_speedtest(n_clicks, server_selection, custom_server_id, current_trigger):
    if n_clicks > 0:
        server_id = custom_server_id if server_selection == 'custom' else server_selection
        
        if not server_id:
            return 'Please enter a valid server ID', {
                'marginTop': '20px',
                'padding': '15px',
                'backgroundColor': '#ffebee',
                'borderRadius': '4px',
                'color': '#c62828',
                'fontSize': '14px',
                'fontWeight': '500',
                'display': 'block'
            }, current_trigger, False
        
        try:
            # Note: insert_speedtest will automatically calculate and store only the average run
            df = Speedtest().run_test(server_id=int(server_id), num_of_runs=3)
            insert_speedtest(df)
            
            # Since insert_speedtest performs averaging, let's fetch the last inserted average to display in the success message
            avg_dl = df['Download Bandwidth (Mbps)'].mean()
            avg_ul = df['Upload Bandwidth (Mbps)'].mean()
            
            return f'Speedtest completed successfully! Average of 3 runs - Download: {avg_dl:.2f} Mbps, Upload: {avg_ul:.2f} Mbps', {
                'marginTop': '20px',
                'padding': '15px',
                'backgroundColor': '#e8f5e9',
                'borderRadius': '4px',
                'color': '#2e7d32',
                'fontSize': '14px',
                'fontWeight': '500',
                'display': 'block'
            }, current_trigger + 1, False
        except Exception as e:
            return f'Error running speedtest: {str(e)}', {
                'marginTop': '20px',
                'padding': '15px',
                'backgroundColor': '#ffebee',
                'borderRadius': '4px',
                'color': '#c62828',
                'fontSize': '14px',
                'fontWeight': '500',
                'display': 'block'
            }, current_trigger, False
    
    return '', {'display': 'none'}, current_trigger, False


if __name__ == '__main__':
    init_database()
    app.run(debug=True, port=8050)
