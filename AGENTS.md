# AGENTS.md

## Setup
```bash
make          # pip install -r requirements.txt
```
Download Speedtest CLI binary from https://www.speedtest.net/apps/cli and place in `bin/speedtest`.

## Running Speed Tests
```bash
python speedtest.py                          # speedtest, 3 runs, Telstra Melbourne
python speedtest.py -m iperf -n 10           # iperf mode, 10 runs
python speedtest.py -l syd                   # speedtest to Telstra Sydney
python speedtest.py -s <server_id_or_ip>     # custom server
```

### CLI Flags
- `-m`: `speedtest`/`iperf` (or shorthand `s`/`i`)
- `-n`: number of test iterations (default: 3)
- `-l`: location preset (`mel` = Telstra Melbourne 12491, `syd` = Telstra Sydney 12492)
- `-s`: custom server ID or IP (overrides `-l`)

## Architecture
- `speedtest.py`: CLI entry point, parses args, calls wrappers, stores results in SQLite
- `wrappers/`: Core libraries (imported via `wrappers/__init__.py`)
  - `speedtest_auto.py`: `Speedtest` class — shells out to `bin/speedtest` binary, parses JSON output
  - `iperf3_auto.py`: `Iperf3Auto` class — uses `iperf3` Python library (requires iperf3 server running)
  - `database.py`: SQLite wrapper, stores results in `results/speedtest.db`. Multi-run inserts are averaged to a single row.
- `tools/`: Analysis and visualization apps
  - `analysis.py`: Shared analysis utilities (result summarization, graph building) used by the Dash app
  - `dash_app.py`: Dash dashboard with server selection and inline test execution (launch via `analyse_results.sh`)
  - `migrate_csv.py`: One-shot script to import legacy CSV results into SQLite
- `results/`: Output directory containing `speedtest.db` and legacy CSV files

## Key Details
- Results are stored in SQLite (`results/speedtest.db`), not CSV. The DB is auto-initialized on first run.
- `insert_speedtest()` and `insert_iperf()` in `database.py` collapse multi-run DataFrames into a single averaged row before inserting.
- Bandwidth values from the speedtest binary are in bytes/sec and divided by 125000 to get Mbps (`speedtest_auto.py:56-57`).
- iPerf tests use 10 parallel streams (`iperf3_auto.py:24`) and require a running iperf3 server on the target host.
- The Dash app (`tools/dash_app.py`) can run speedtests inline from the browser and auto-refreshes every 60s when enabled.