# SpeedTest-Automated

Script + Libraries used to run both SpeedTest + iPerf tests in bulk, record the output, then Graph the results. Really is just a fancy wrapper to automate a lot of the tests I do en masse for work.

once the CLI Portion of the tool is complete, hopefully we can work towards building out a Django / Flask app so we can get a WEB GUI / (Electron GUI Maybe?)

## To-Do

### Priority 1:
- Refactor Existing Code to new Format - DONE
- Split out into Libraries - DONE
- Rebuild the CLI into something a bit more user friendly - DONE
- Port Graphs to something a bit more dynamic + User Friendly. - plotly implementation parially done.

### Priority 2 / Optional:
- Either use Dash or Flask to build a basic Web GUI for 
    - Analytics
    - Running Basic Speedtests
    - These might require their own seperate projects.


# Installation

use the makefile if possible with 
```
make
```

if not the command should simply be "pip install -r requirements.txt"


## Usage
 The Script can be run with:
```
/PATH/TO/Speedtest-Automated/speedtest.py
```
### Flags:
-m: sets mode, either iPerf or Speedtest.net

-s: sets server, either IP / Hostname for iPerf or Server ID for speedtest. Default for speedtest is Telstra's Melbourne Server.

-n: number of runs, adjusts the amount of times the script will test.

-o: output file, name the file it is to output.
