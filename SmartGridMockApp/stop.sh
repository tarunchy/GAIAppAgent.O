#!/bin/bash
APP_DIR="/home/dlyog/ted/omniagent/SmartGridMockApp"
PID_FILE="$APP_DIR/pid.file"

if [ -f $PID_FILE ]; then
    PID=$(cat $PID_FILE)
    if ps -p $PID > /dev/null; then
        kill $PID
        rm -f $PID_FILE
        echo "Application stopped."
    else
        echo "Process with PID $PID not found. Removing stale PID file."
        rm -f $PID_FILE
    fi
else
    echo "No PID file found. Attempting to find the process manually."
    PID=$(ps -ef | grep "[p]ython $APP_DIR/app.py" | awk '{print $2}')
    if [ -n "$PID" ]; then
        kill $PID
        echo "Application stopped. PID was $PID."
    else
        echo "Application not running."
    fi
fi
