#!/bin/bash
# Simple script to start the FastAPI server in the background

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start server with nohup (background process)
echo "Starting AI Medical Assistant server..."
echo "Server will run in the background."
echo "Logs will be written to server.log"
echo ""
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# Get the process ID
PID=$!
echo "Server started with PID: $PID"
echo ""
echo "To view logs: tail -f server.log"
echo "To stop the server: kill $PID"
echo "Or find and kill: ps aux | grep uvicorn"
echo ""
echo "Server accessible at: http://$(hostname -I | awk '{print $1}'):8000"

