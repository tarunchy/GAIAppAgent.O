#!/bin/bash

APP_DIR="/home/dlyog/ted/omniagent/SmartGridMockApp"
PID_FILE="$APP_DIR/pid.file"
LOG_FILE="$APP_DIR/output.log"
APP_COMMAND="python app.py"

cd $APP_DIR

# Check if the application is already running
if [ -f $PID_FILE ]; then
  PID=$(cat $PID_FILE)
  if ps -p $PID > /dev/null; then
    echo "Application is already running with PID $PID. Stopping it first."
    kill $PID
    if [ $? -eq 0 ]; then
      echo "Application stopped."
      rm -f $PID_FILE
    else
      echo "Failed to stop the application. Exiting."
      exit 1
    fi
  else
    echo "PID file exists but process is not running. Removing stale PID file."
    rm -f $PID_FILE
  fi
fi

# Start the application
nohup $APP_COMMAND > $LOG_FILE 2>&1 &
NEW_PID=$!
echo $NEW_PID > $PID_FILE
echo "Application started with PID $NEW_PID."
