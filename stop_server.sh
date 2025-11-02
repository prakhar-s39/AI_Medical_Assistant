#!/bin/bash
# Script to stop the FastAPI server (Ollama stays running if it's a service)

echo "Stopping AI Medical Assistant..."

# Stop FastAPI server
echo "Stopping FastAPI server..."
PIDS=$(ps aux | grep "uvicorn app:app" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "   No server process found."
else
    for PID in $PIDS; do
        echo "   Killing server process $PID..."
        kill $PID 2>/dev/null
    done
    echo "✅ Server stopped."
fi

# Remove server PID file if it exists
if [ -f "server.pid" ]; then
    rm server.pid
fi

echo ""

# Handle Ollama - only stop if we started it directly (has PID file)
if [ -f "ollama.pid" ]; then
    OLLAMA_PID=$(cat ollama.pid)
    if ps -p $OLLAMA_PID > /dev/null 2>&1; then
        echo "Stopping Ollama (started by script)..."
        kill $OLLAMA_PID 2>/dev/null
        rm ollama.pid
        echo "✅ Ollama stopped."
    else
        echo "   Ollama process not found (already stopped)"
        rm ollama.pid
    fi
else
    # Ollama is running as a service or separately
    if systemctl is-active --quiet ollama 2>/dev/null || pgrep -x ollama > /dev/null; then
        echo "ℹ️  Ollama is still running (as service)"
        echo "   This is normal - Ollama will continue running"
        echo "   To stop Ollama: sudo systemctl stop ollama"
    fi
fi

# Show log info
if [ -f "ollama.log" ]; then
    echo ""
    echo "📝 Ollama logs are preserved in ollama.log"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All services stopped"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

