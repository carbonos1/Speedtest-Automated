#!/usr/bin/env python3
'''Plotly-based graphing of test results from the SQLite database.
'''
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.analysis import build_graph, get_results_summary


def main():
    parser = argparse.ArgumentParser(description='Generate Plotly graphs from stored test results')
    parser.add_argument('-t', '--title', default='Speedtest Results',
                        help='Plot title (default: "Speedtest Results")')
    args = parser.parse_args()

    results = get_results_summary()
    if results.empty:
        print('No data available in the database.')
        return

    results.to_excel('results/iPerfSummary.xlsx')

    print(f'\n----------\nAverages Output:\n----------\n {results}')

    fig = build_graph(results)
    fig.update_layout(title=args.title)

    fig.show()
    fig.write_image(f'results/{args.title}.png')
    fig.write_image(f'results/{args.title}.svg')


if __name__ == "__main__":
    main()
