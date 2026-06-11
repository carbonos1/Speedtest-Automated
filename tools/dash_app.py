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
    html.H1('Throughput Performance Graph', style={'marginBottom': '20px'}),
    
    html.Div([
        html.Button('Run Speed Test', id='run-test-btn', n_clicks=0, 
                   style={'marginRight': '10px', 'padding': '8px 16px'}),
        dcc.Checklist(
            id='autorefresh-toggle',
            options=[{'label': ' Enable Auto Refresh', 'value': 'enabled'}],
            value=[],
            style={'display': 'inline-block', 'padding': '8px'}
        ),
    ], style={'marginBottom': '20px'}),
    
    dcc.Interval(
        id='refresh-interval',
        interval=60000,
        disabled=True,
        n_intervals=0
    ),
    
    dcc.Graph(id='performance-graph', style={'height': '800px'}),
    
    html.H2('Throughput Performance Table', style={'marginTop': '40px', 'marginBottom': '20px'}),
    
    dash_table.DataTable(
        id='results-table',
        page_size=20,
        sort_action='native',
        filter_action='native',
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'backgroundColor': 'white'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        },
        style_data_conditional=[{
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        }]
    )
], style={'maxWidth': '100%', 'padding': '20px'})


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
            plot_bgcolor='white'
        )
        return fig, [], []
    
    fig = build_graph(results)
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
