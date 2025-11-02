#!/bin/bash
# Script to stop the FastAPI server

echo "Stopping AI Medical Assistant server..."

# Find and kill uvicorn processes
PIDS=$(ps aux | grep "uvicorn app:app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No server process found."
else
    for PID in $PIDS; do
        echo "Killing process $PID..."
        kill $PID
    done
    echo "Server stopped."
fi

