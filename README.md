# SpeedTest-Automated

Script + Libraries used to run both SpeedTest + iPerf tests in bulk, record the output, then Graph the results. Really is just a fancy wrapper to automate a lot of the tests I do en masse.

a basic interactive tool has been written using streamlit to perform basic analysis.

![Web screenshot](https://i.imgur.com/Sau1BOa.png)

## To-Do

### Priority 1:


### Priority 2 / Optional:
- Either use Dash or Flask to build a basic Web GUI for 
    - Analytics
    - Running Basic Speedtests
    - These might require their own seperate projects.


# Installation

1. use the makefile if possible with 
```
make
```
if not the command should simply be "pip install -r requirements.txt"

2. Download the relevant speedtest binary from the [speedtest cli website](https://www.speedtest.net/apps/cli) and place it in the 'bin' folder.


## Usage

### CLI
 The CLI Script can be run with:
```
/PATH/TO/Speedtest-Automated/speedtest.py
```

Use this to generate tests.

### Web GUI

Run the relevant 'analyse_results' file depending on your choice of OS (.sh for linux / MacOS, .bat for windows)

### Flags:
-m: sets mode, either iPerf or Speedtest.net

-s: sets server, either IP / Hostname for iPerf or Server ID for speedtest. Default for speedtest is Telstra's Melbourne Server.

-n: number of runs, adjusts the amount of times the script will test.

-o: output file, name the file it is to output.
