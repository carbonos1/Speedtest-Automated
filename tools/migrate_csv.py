#!/usr/bin/env python3
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrappers.database import init_database, migrate_csv_to_db

def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy CSV result files into the SQLite database"
    )
    parser.add_argument(
        '-d', '--dir',
        type=str,
        default=None,
        help='Path to results directory (default: results/)'
    )
    args = parser.parse_args()

    init_database()
    print('Migrating CSV files to SQLite database...')
    migrate_csv_to_db(results_dir=args.dir)
    print('Migration complete.')

if __name__ == '__main__':
    main()
