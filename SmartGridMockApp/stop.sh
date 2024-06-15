#!/bin/bash
if [ -f pid.file ]; then
    kill $(cat pid.file)
    rm -f pid.file
    echo "Application stopped."
else
    echo "No pid file found. Is the application running?"
fi
EOF
