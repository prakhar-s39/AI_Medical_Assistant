#!/bin/bash
# Simple script to start the FastAPI server and Ollama in the background

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting AI Medical Assistant setup..."
echo ""

# Set Ollama performance environment variables
export OLLAMA_NUM_PARALLEL=1
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_KEEP_ALIVE=5m

# Check and start Ollama if needed
echo "Checking Ollama..."

# Check if Ollama service is running
if systemctl is-active --quiet ollama 2>/dev/null; then
    echo "✅ Ollama service is already running"
elif pgrep -x ollama > /dev/null; then
    echo "✅ Ollama process is already running"
else
    echo "Starting Ollama service..."
    if command -v systemctl &> /dev/null && systemctl is-enabled ollama &> /dev/null; then
        # Try to start as service (preferred)
        sudo systemctl start ollama
        sleep 2  # Give it time to start
        if systemctl is-active --quiet ollama 2>/dev/null; then
            echo "✅ Ollama service started"
        else
            echo "⚠️  Failed to start Ollama service, trying direct run..."
            # Fallback: run Ollama directly in background
            nohup ollama serve > ollama.log 2>&1 &
            OLLAMA_PID=$!
            echo $OLLAMA_PID > ollama.pid
            echo "✅ Ollama started in background (PID: $OLLAMA_PID)"
        fi
    else
        # No systemctl or service not configured, run directly
        echo "Starting Ollama directly..."
        nohup ollama serve > ollama.log 2>&1 &
        OLLAMA_PID=$!
        echo $OLLAMA_PID > ollama.pid
        echo "✅ Ollama started in background (PID: $OLLAMA_PID)"
        echo "   Logs: tail -f ollama.log"
    fi
    sleep 2  # Wait for Ollama to initialize
fi

# Verify Ollama is accessible
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is accessible"
else
    echo "⚠️  Warning: Ollama may not be fully ready yet"
    echo "   It might take a few more seconds to initialize"
fi

echo ""
echo "Starting FastAPI server..."

# Start server with nohup (background process)
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &

# Get the process ID
PID=$!
echo $PID > server.pid
echo "✅ Server started with PID: $PID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Service Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FastAPI Server: Running (PID: $PID)"
if [ -f "ollama.pid" ]; then
    OLLAMA_PID=$(cat ollama.pid)
    echo "Ollama: Running (PID: $OLLAMA_PID)"
elif systemctl is-active --quiet ollama 2>/dev/null; then
    echo "Ollama: Running (systemd service)"
fi
echo ""
echo "📊 Logs:"
echo "   Server: tail -f server.log"
if [ -f "ollama.log" ]; then
    echo "   Ollama: tail -f ollama.log"
fi
echo ""
echo "🌐 Server accessible at: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "🛑 To stop everything: ./stop_server.sh"

