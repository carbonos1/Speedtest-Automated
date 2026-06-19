# SpeedTest-Automated

A comprehensive toolkit for running, recording, and analyzing Speedtest.net and iPerf3 network performance tests.

## Features

- **Automated Testing**: Run bulk Speedtest.net or iPerf3 tests with configurable iterations
- **SQLite Storage**: All results stored in `results/speedtest.db` with automatic CSV migration on first run
- **Dash Web Dashboard**: Interactive web interface for analysis and running tests directly from the browser
- **Flexible Server Selection**: Predefined servers (Telstra Melbourne/Sydney, GigaComm) or custom server IDs
- **Performance Visualization**: Real-time graphs showing download/upload throughput, latency, and jitter

![Web Dashboard](https://i.imgur.com/Sau1BOa.png)

## Installation

1. Install dependencies:
```bash
make
# or
pip install -r requirements.txt
```

2. Download the Speedtest CLI binary from [speedtest.net](https://www.speedtest.net/apps/cli) and place it in the `bin/` folder.

## Usage

### Command Line Interface

Run speed tests from the terminal:

```bash
python speedtest.py                          # Default: Speedtest, 3 runs, Telstra Melbourne
python speedtest.py -m iperf -n 10           # iPerf mode, 10 runs
python speedtest.py -l syd                   # Speedtest to Telstra Sydney
python speedtest.py -s <server_id_or_ip>     # Custom server
```

**CLI Flags:**
- `-m, --mode`: Test mode - `speedtest`/`s` or `iperf`/`i` (default: speedtest)
- `-n, --num-of-runs`: Number of test iterations (default: 3)
- `-l, --location`: Location preset - `mel` (Telstra Melbourne) or `syd` (Telstra Sydney)
- `-s, --server-id`: Custom server ID or IP address (overrides `-l`)

### Web Dashboard

Launch the Dash web interface:

```bash
# Linux/Mac
./analyse_results.sh

# Windows
analyse_results.bat
```

The dashboard runs on `http://localhost:8050` and provides:
- **Server Selection**: Choose from predefined servers or enter a custom server ID
- **Inline Testing**: Run speedtests directly from the browser
- **Auto-Refresh**: Optional 60-second auto-refresh for continuous monitoring
- **Interactive Graphs**: Plotly-based visualizations with zoom and hover details
- **Data Table**: Sortable and filterable results table

## Architecture

- `speedtest.py`: CLI entry point with automatic CSV-to-SQLite migration on first run
- `wrappers/`: Core testing libraries
  - `speedtest_auto.py`: Shells out to `bin/speedtest` binary, parses JSON output
  - `iperf3_auto.py`: Uses `iperf3` Python library (requires iperf3 server running)
  - `database.py`: SQLite wrapper with automatic multi-run averaging
- `tools/`: Analysis and visualization
  - `analysis.py`: Shared analysis utilities (result summarization, graph building)
  - `dash_app.py`: Dash web dashboard
  - `migrate_csv.py`: Standalone CSV migration tool
- `results/`: Output directory containing `speedtest.db` and legacy CSV files

## Data Storage

Results are stored in SQLite (`results/speedtest.db`). When multiple test runs are performed, they are automatically averaged into a single database row for cleaner analysis.

On first run, if the database is empty and legacy CSV files exist in `results/`, they are automatically migrated to SQLite.

## Additional Tools

- `tools/ping_dash_app.py`: Separate Dash app for continuous ping monitoring with latency/jitter/packet loss graphs
- `tools/iPerfGraph.py`: Matplotlib-based iPerf result graphing
- `tools/migrate_csv.py`: Manual CSV-to-SQLite migration tool
- `tools/migrate_to_sessions.py`: One-shot migration from legacy tables to the session/run schema (dry-run supported)

## Security Note

The Dash dashboard (`tools/dash_app.py`) is currently configured with `debug=True` and `host='0.0.0.0'`. This exposes the Werkzeug debugger to the network, which can allow arbitrary code execution if the debugger PIN is obtained. For production or LAN-exposed deployments, bind to `127.0.0.1` and set `debug=False`. A future phase will add authentication.
