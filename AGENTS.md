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
python speedtest.py -m tr143 --download-url URL --upload-url URL --upload-file FILE
python speedtest.py -l syd                   # speedtest to Telstra Sydney
python speedtest.py -s <server_id_or_ip>     # custom server
```

### CLI Flags
- `-m`: `speedtest`/`iperf`/`tr143` (or shorthand `s`/`i`)
- `-n`: number of test iterations (default: 3)
- `-l`: location preset (`mel` = Telstra Melbourne 12491, `syd` = Telstra Sydney 12492)
- `-s`: custom server ID or IP (overrides `-l`)
- `--download-url`, `--upload-url`, `--upload-file`, `--ping-host`: TR-143 mode options

## Testing & Linting
```bash
make test     # pytest tests/ -v
make lint     # ruff check .
make format   # ruff format .
```

## Architecture
- `speedtest.py`: CLI entry point, parses args, calls wrappers, stores results in SQLite
- `wrappers/`: Core libraries (imported via `wrappers/__init__.py`)
  - `speedtest_auto.py`: `Speedtest` class — shells out to `bin/speedtest` binary via `subprocess.run`, parses JSON output with key-error guards
  - `iperf3_auto.py`: `Iperf3Auto` class — uses `iperf3` Python library (requires iperf3 server running)
  - `tr143.py`: `TR143Tester` class — TR-143 HTML-based server testing (download/upload/latency)
  - `database.py`: SQLite wrapper, stores results in `results/speedtest.db`. Uses session/run model: one `test_sessions` row per invocation + N `test_runs` rows per session
  - `utils.py`: Shared helpers (`bps_to_mbps`, `Bps_to_mbps`, `setup_logging`)
- `tools/`: Analysis and visualization apps (imported via `tools/__init__.py`)
  - `analysis.py`: Shared analysis utilities (session-level result summarization, graph building)
  - `dash_app.py`: Dash dashboard with server selection, background-thread test execution, and auto-refresh (launch via `analyse_results.sh`)
  - `ping_dash_app.py`: Dash app for continuous ping monitoring (launch via `analyse_ping.sh`)
  - `migrate_csv.py`: One-shot script to import legacy CSV results into SQLite
  - `migrate_to_sessions.py`: Migrate legacy tables to session/run schema with dry-run support
  - `iPerfGraph.py`: Matplotlib-based result graphing (reads from SQLite, `--title` CLI arg)
  - `plotlygraph.py`: Plotly-based result graphing (reads from SQLite, `--title` CLI arg)
- `tests/`: Unit tests (database, speedtest wrapper, analysis)
- `results/`: Output directory containing `speedtest.db` and legacy CSV files

## Key Details
- Results are stored in SQLite (`results/speedtest.db`), not CSV. The DB is auto-initialized on first run.
- `insert_session(df, mode)` in `database.py` creates one `test_sessions` row (with pre-computed averages) + N `test_runs` rows, preserving every individual run. Replaces the legacy averaged-insert model.
- Legacy tables (`speedtest_results_legacy`, `iperf_results_legacy`) are kept for verification after migration via `tools/migrate_to_sessions.py`.
- Bandwidth values from the speedtest binary are in bytes/sec, converted via `Bps_to_mbps()` in `wrappers/utils.py`. iPerf values are in bits/sec, converted via `bps_to_mbps()`.
- iPerf tests use 10 parallel streams and require a running iperf3 server on the target host.
- The Dash app runs speedtests in a background thread with 2s polling for completion, preventing UI freezes.
- The Dash app is configured with `debug=True` and `host='0.0.0.0'` — see the Security Note in README.md.
