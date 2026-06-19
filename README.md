# SpeedTest-Automated

A comprehensive toolkit for running, recording, and analyzing Speedtest.net, iPerf3, and TR-143 network performance tests.

## Features

- **Automated Testing**: Run bulk Speedtest.net, iPerf3, or TR-143 tests with configurable iterations
- **Session/Run Data Model**: Each invocation creates a session with N individual run rows, preserving per-run detail
- **SQLite Storage**: All results stored in `results/speedtest.db` with automatic CSV migration on first run
- **Dash Web Dashboard**: Interactive web interface for analysis and running tests directly from the browser
- **Flexible Server Selection**: Predefined servers (Telstra Melbourne/Sydney, GigaComm) or custom server IDs
- **Performance Visualization**: Real-time graphs showing download/upload throughput, latency, and jitter
- **Background Test Execution**: Dash app runs tests in a background thread with progress polling

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
python speedtest.py -m tr143 --download-url URL --upload-url URL --upload-file FILE
python speedtest.py -l syd                   # Speedtest to Telstra Sydney
python speedtest.py -s <server_id_or_ip>     # Custom server
```

**CLI Flags:**
- `-m, --mode`: Test mode - `speedtest`/`s`, `iperf`/`i`, or `tr143` (default: speedtest)
- `-n, --num-of-runs`: Number of test iterations (default: 3)
- `-l, --location`: Location preset - `mel` (Telstra Melbourne) or `syd` (Telstra Sydney)
- `-s, --server-id`: Custom server ID or IP address (overrides `-l`)
- `--download-url`, `--upload-url`, `--upload-file`, `--ping-host`: TR-143 mode options

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
- **Inline Testing**: Run speedtests directly from the browser (background thread, non-blocking)
- **Auto-Refresh**: Optional 60-second auto-refresh for continuous monitoring
- **Interactive Graphs**: Plotly-based visualizations with zoom and hover details
- **Data Table**: Sortable and filterable results table
- **CSV Export**: Download results as CSV

### Ping Monitoring

```bash
# Linux/Mac
./analyse_ping.sh

# Windows
analyse_ping.bat
```

A separate Dash app for continuous ping monitoring with latency, jitter, and packet loss graphs.

### Graphing Tools

```bash
python tools/iPerfGraph.py --title "My Results"    # Matplotlib graphs
python tools/plotlygraph.py --title "My Results"   # Plotly graphs
```

### Migration Tools

```bash
# Migrate legacy CSV files to SQLite
python tools/migrate_csv.py

# Migrate legacy tables to session/run schema (dry-run first)
python tools/migrate_to_sessions.py
python tools/migrate_to_sessions.py --apply
```

## Architecture

- `speedtest.py`: CLI entry point with automatic CSV-to-SQLite migration on first run
- `wrappers/`: Core testing libraries
  - `speedtest_auto.py`: Shells out to `bin/speedtest` binary via `subprocess.run`, parses JSON output with error guards
  - `iperf3_auto.py`: Uses `iperf3` Python library (requires iperf3 server running)
  - `tr143.py`: TR-143 HTML-based server testing (download/upload/latency)
  - `database.py`: SQLite wrapper with session/run data model
  - `utils.py`: Shared helpers (bandwidth conversions, logging setup)
- `tools/`: Analysis and visualization
  - `analysis.py`: Shared analysis utilities (session-level result summarization, graph building)
  - `dash_app.py`: Dash web dashboard with background-thread test execution
  - `ping_dash_app.py`: Dash app for continuous ping monitoring
  - `migrate_csv.py`: Standalone CSV migration tool
  - `migrate_to_sessions.py`: Legacy-to-session/run migration with dry-run support
  - `iPerfGraph.py`: Matplotlib-based result graphing (reads from SQLite)
  - `plotlygraph.py`: Plotly-based result graphing (reads from SQLite)
- `tests/`: Unit tests (database, speedtest wrapper, analysis)
- `results/`: Output directory containing `speedtest.db` and legacy CSV files

## Data Storage

Results are stored in SQLite (`results/speedtest.db`) using a session/run model:

- **`test_sessions`**: One row per invocation with pre-computed averages and session metadata
- **`test_runs`**: N rows per session, preserving every individual run with full attributes

On first run, if the database is empty and legacy CSV files exist in `results/`, they are automatically migrated to SQLite.

Legacy tables (`speedtest_results_legacy`, `iperf_results_legacy`) are retained after migration for verification.

## Testing & Linting

```bash
make test     # pytest tests/ -v
make lint     # ruff check .
make format   # ruff format .
```

## Security Note

The Dash dashboard (`tools/dash_app.py`) is currently configured with `debug=True` and `host='0.0.0.0'`. This exposes the Werkzeug debugger to the network, which can allow arbitrary code execution if the debugger PIN is obtained. For production or LAN-exposed deployments, bind to `127.0.0.1` and set `debug=False`. A future phase will add authentication.
