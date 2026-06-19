#!/usr/bin/env python3
'''Matplotlib-based graphing of test results from the SQLite database.
'''
import argparse
import os
import sys

import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.analysis import get_results_summary


def main():
    parser = argparse.ArgumentParser(description='Generate matplotlib graphs from stored test results')
    parser.add_argument('-t', '--title', default='Speedtest Results',
                        help='Plot title (default: "Speedtest Results")')
    args = parser.parse_args()

    results = get_results_summary()
    if results.empty:
        print('No data available in the database.')
        return

    results.to_excel('results/iPerfSummary.xlsx')

    print(f'\n----------\nAverages Output:\n----------\n {results}')

    ax = results.plot(x='file', y='Download Bandwidth (Mbps)', label='Download (in Mbps)', figsize=(10, 5))
    results.plot(x='file', y='Upload Bandwidth (Mbps)', label='Upload (in Mbps)', ax=ax)
    ax.scatter(x=results['file'], y=results['Download Bandwidth (Mbps)'])
    ax.scatter(x=results['file'], y=results['Upload Bandwidth (Mbps)'])

    for i, j in zip(results['file'], results['Download Bandwidth (Mbps)']):
        ax.annotate(str(round(j, 2)), xy=(i, j))

    for i, j in zip(results['file'], results['Upload Bandwidth (Mbps)']):
        ax.annotate(str(round(j, 2)), xy=(i, j))

    ax.grid()
    plt.setp(ax.get_xticklabels(), rotation=10, ha="right")
    plt.title(args.title)

    plt.savefig(f'results/{args.title}.png')
    plt.savefig(f'results/{args.title}.svg')


if __name__ == "__main__":
    main()
