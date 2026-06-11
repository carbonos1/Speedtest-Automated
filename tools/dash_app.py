#!/usr/bin/env python3
from dash import Dash, dcc, html, dash_table, Input, Output, State, callback, ctx
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrappers.database import init_database, insert_speedtest
from wrappers import Speedtest
from tools.analyse_results import get_results_summary, build_graph

app = Dash(__name__)

app.layout = html.Div([
    html.H1('Throughput Performance Dashboard', 
            style={'marginBottom': '30px', 'color': '#1a1a1a', 'fontSize': '2.5rem'}),
    
    html.Div([
        html.Button('Run Speed Test', id='run-test-btn', n_clicks=0, 
                   style={
                       'marginRight': '20px', 
                       'padding': '12px 24px',
                       'backgroundColor': '#0066cc',
                       'color': 'white',
                       'border': 'none',
                       'borderRadius': '4px',
                       'cursor': 'pointer',
                       'fontSize': '14px',
                       'fontWeight': '500'
                   }),
        dcc.Checklist(
            id='autorefresh-toggle',
            options=[{'label': ' Enable Auto Refresh (60s)', 'value': 'enabled'}],
            value=[],
            style={
                'display': 'inline-block', 
                'padding': '12px',
                'color': '#333333',
                'fontSize': '14px'
            }
        ),
    ], style={
        'marginBottom': '30px',
        'padding': '20px',
        'backgroundColor': '#f5f5f5',
        'borderRadius': '8px',
        'border': '1px solid #e0e0e0'
    }),
    
    dcc.Interval(
        id='refresh-interval',
        interval=60000,
        disabled=True,
        n_intervals=0
    ),
    
    dcc.Graph(id='performance-graph', style={'height': '800px'}),
    
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
    [Output('performance-graph', 'figure'),
     Output('results-table', 'data'),
     Output('results-table', 'columns')],
    [Input('refresh-interval', 'n_intervals'),
     Input('run-test-btn', 'n_clicks')],
    prevent_initial_call=False
)
def update_dashboard(n_intervals, n_clicks):
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
    
    table_data = results.to_dict('records')
    table_columns = [{'name': col, 'id': col} for col in results.columns]
    
    return fig, table_data, table_columns


@callback(
    Output('refresh-interval', 'disabled'),
    Input('autorefresh-toggle', 'value')
)
def toggle_autorefresh(value):
    return 'enabled' not in value


@callback(
    Output('run-test-btn', 'children'),
    Input('run-test-btn', 'n_clicks'),
    prevent_initial_call=True
)
def run_speedtest(n_clicks):
    if n_clicks > 0:
        df = Speedtest().run_test(num_of_runs=3)
        insert_speedtest(df)
    return 'Run Speed Test'


if __name__ == '__main__':
    init_database()
    app.run(debug=True, port=8050)
