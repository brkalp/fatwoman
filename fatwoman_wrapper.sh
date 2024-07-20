# Define a variable for the directory path
export BASE_DIR="/media/fatwoman/15GB/"
export FATBOY_DIR="/media/fatwoman/fatboy/"
export LOG_DIR=$FATBOY_DIR"/logs/"
alias 15GB='cd $BASE_DIR'
alias FATBOY='cd $FATBOY_DIR'
WRAPPER() { nano ${BASE_DIR}fatwoman_wrapper.sh; }
echo "$(date): Wrapper script started" > $LOG_DIR"0_wrapper_echo.log"
export PYTHONPATH="$PYTHONPATH:${BASE_DIR}Scripts_Setup_Logger/:${BASE_DIR}/Scripts_Setup_Dirs/"
export PYTHONPATH="/media/fatwoman/fatboy/python_libraries:$PYTHONPATH"
RETURNIP() { curl ifconfig.me; }
IPGET() { curl ifconfig.me; }
SETKEYBOARDSWE() { setxkbmap se; }
screensdimon(){
DISPLAY=:0 xrandr --output DisplayPort-0 --brightness 0.55
DISPLAY=:0 xrandr --output DisplayPort-1 --brightness 0.55
}
screensdimoff(){
DISPLAY=:0 xrandr --output DisplayPort-0 --brightness 1
DISPLAY=:0 xrandr --output DisplayPort-1 --brightness 1
}
logs()        { less ${LOG_DIR}Total.txt; }
logfolder()   { cd ${LOG_DIR}; }
logsarchive() { ${LOG_DIR}archive_here.sh; }
screensoff()  { DISPLAY=:0 xrandr --output DisplayPort-0 --off --output DisplayPort-1 --off; }
screenson()   { DISPLAY=:0 xrandr --output DisplayPort-1 --auto --rotate right --output DisplayPort-0 --auto --rotate left --left-of DisplayPort-1 --primary; }
surferkill() {
    pkill -f Surfer.py
    pkill -f mozilla
    }
surfer()             { DISPLAY=:0 /usr/bin/python3 ${BASE_DIR}Scripts_Surfer/Surfer.py > /dev/null 2>&1 & }
surferprint()        { DISPLAY=:0 /usr/bin/python3 ${BASE_DIR}Scripts_Surfer/Surfer.py; }
surferbbg()          { DISPLAY=:0 /usr/bin/python3 ${BASE_DIR}Scripts_Surfer/Surfer.py --bbg; }
runCVIXScrape()      { /usr/bin/python3 ${BASE_DIR}Scripts_Data_Feeds/VIX_Central_Scrape.py;}
runCBOEScrape()      { /usr/bin/python3 ${BASE_DIR}Scripts_Data_Feeds/CBOE_Scrape.py;}
runYahooDownload()   { /usr/bin/python3 ${BASE_DIR}Scripts_Generate_Daily_Plots/YahooDownload.py; }
runYahooInfo()       { /usr/bin/python3 ${BASE_DIR}Scripts_Generate_Daily_Plots/Yahoo_Info.py;}
runYahooPlotter()    { /usr/bin/python3 ${BASE_DIR}Scripts_Generate_Daily_Plots/YahooPlotter.py; }
runYahooFXConvert()  { /usr/bin/python3 ${BASE_DIR}Scripts_Generate_Daily_Plots/df_FX_Convert.py; }
runModelDownload()   { /usr/bin/python3 ${BASE_DIR}Scripts_Model/ModelDownload.py; }
runBinanceDownload() { /usr/bin/python3 ${BASE_DIR}Scripts_Binance/binance_orderbook_save.py; }
runYCFREDDownload()  { /usr/bin/python3 ${BASE_DIR}Scripts_Yield_Curve/YC_FRED_Download.py; }
runYCQuantlibPlot()  { /usr/bin/python3 ${BASE_DIR}Scripts_Yield_Curve/YC_Quantlib_int.py; }
runYCScipyPlot()     { /usr/bin/python3 ${BASE_DIR}Scripts_Yield_Curve/YC_scipy_int.py; }
runYCAppend()        { /usr/bin/python3 ${BASE_DIR}Scripts_Yield_Curve/YC_Append.py; }
runVolDownload()     { /usr/bin/python3 ${BASE_DIR}Scripts_Vol_Surface/get_vol_chains.py; }
runVolPlot()         { /usr/bin/python3 ${BASE_DIR}Scripts_Vol_Surface/plot_vol_chains.py; }
runSODpy()           { /usr/bin/python3 ${BASE_DIR}Utility/SOD_print.py;}
runEODpy()           { /usr/bin/python3 ${BASE_DIR}Utility/EOD_print.py;}
runChromeRemoteDesktop() { sudo systemctl start chrome-remote-desktop@fatwoman.service; }
runChromeRemoteDesktopkill() { /opt/google/chrome-remote-desktop/chrome-remote-desktop --stop;}
runChromeRemoteDesktopstatus() { systemctl status chrome-remote-desktop@fatwoman.service;}

runBatchHourly() {
    runCBOEScrape
    runCVIXScrape
}

runBatchDaily()  {
    runSODpy
    runChromeRemoteDesktop
    # Base Daily plots
    runYahooDownload
    runYahooFXConvert
    runYahooPlotter
    # Yield Curve
    runYCFREDDownload
    runYCQuantlibPlot
    runYCScipyPlot
    runYCAppend
    # Volas
    runVolDownload
    runVolPlot
}
runBatchMorning1() {
    surferkill
    screenson
    screensdimon
    surferbbg
}
runBatchMorning2() {
    surferkill
    surferprint
    screensdimon
    }
runBatchEvening() {
    surferkill
    screensoff
    }
runBatchEOD(){
    logsarchive
    runEODpy
    }
echo "$(date): Wrapper script finished" >> $LOG_DIR"0_wrapper_echo.log"
