# AI Medical Assistant - Raspberry Pi 5

A lightweight AI medical assistant backend running locally on Raspberry Pi 5 using Ollama and FastAPI.

## Quick Start (Headless SSH Setup)

**Workflow Overview:**
1. **On Raspberry Pi (via SSH)**: Run the FastAPI server in the background
2. **On Your Laptop**: Access the API using the Pi's IP address

**Quick commands:**

```bash
# On Raspberry Pi (SSH):
cd /home/peter/Coding/raspi
./start_server.sh              # Start server
tail -f server.log             # View logs
./stop_server.sh               # Stop server

# On your laptop:
# Edit test_client.py with Pi's IP, then:
python3 test_client.py         # Test the API
# Or visit in browser:
http://<PI_IP>:8000/docs       # Interactive API docs
```

## Prerequisites

1. **Ollama installed and running locally**
   - Install Ollama: https://ollama.ai/download
   - Pull the `phi3:mini` model:
     ```bash
     ollama pull phi3:mini
     ```
   - Verify Ollama is running:
     ```bash
     ollama list
     ```

2. **Python 3.8+** (should come pre-installed on most Raspberry Pi OS distributions)

## Setup Instructions

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Or if you prefer using a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Verify Ollama is accessible:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

## Running the Server (Headless Setup)

Since you're running the Raspberry Pi headless via SSH, here are several ways to run the server:

### Option 1: Using `screen` (Recommended for quick testing)

**On the Raspberry Pi (via SSH):**
```bash
# Install screen if not already installed
sudo apt install screen

# Start a new screen session
screen -S medical-assistant

# Activate your virtual environment (if using one)
source venv/bin/activate

# Navigate to your project directory
cd /home/peter/Coding/raspi

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8000
```

**To detach from screen (server keeps running):**
- Press `Ctrl+A`, then `D`

**To reattach later:**
```bash
screen -r medical-assistant
```

**To stop the server:**
- Reattach to screen, then press `Ctrl+C`

### Option 2: Using `tmux`

**On the Raspberry Pi (via SSH):**
```bash
# Install tmux if not already installed
sudo apt install tmux

# Start a new tmux session
tmux new -s medical-assistant

# Activate virtual environment and run server
source venv/bin/activate
cd /home/peter/Coding/raspi
uvicorn app:app --host 0.0.0.0 --port 8000
```

**To detach:** `Ctrl+B`, then `D`  
**To reattach:** `tmux attach -t medical-assistant`

### Option 3: Using Helper Scripts (Simplest)

**On the Raspberry Pi (via SSH):**
```bash
cd /home/peter/Coding/raspi

# Start the server in background
./start_server.sh

# View logs
tail -f server.log

# Stop the server
./stop_server.sh
```

### Option 4: Using `nohup` (Manual background process)

**On the Raspberry Pi (via SSH):**
```bash
source venv/bin/activate
cd /home/peter/Coding/raspi
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

**To stop:**
```bash
# Find the process ID
ps aux | grep uvicorn
# Kill it (replace PID with actual process ID)
kill <PID>
```

### Option 5: Systemd Service (Best for production/auto-start)

Create a systemd service file for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/medical-assistant.service
```

Paste the following (adjust paths as needed):
```ini
[Unit]
Description=AI Medical Assistant FastAPI Server
After=network.target

[Service]
Type=simple
User=peter
WorkingDirectory=/home/peter/Coding/raspi
Environment="PATH=/home/peter/Coding/raspi/venv/bin"
ExecStart=/home/peter/Coding/raspi/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable medical-assistant
sudo systemctl start medical-assistant

# Check status
sudo systemctl status medical-assistant

# View logs
sudo journalctl -u medical-assistant -f
```

**Stop/restart:**
```bash
sudo systemctl stop medical-assistant
sudo systemctl restart medical-assistant
```

### Finding Your Raspberry Pi's IP Address

**On the Raspberry Pi:**
```bash
# Method 1: Using hostname
hostname -I

# Method 2: Using ip command
ip addr show | grep "inet "

# Method 3: Check current SSH connection (if already connected)
echo $SSH_CONNECTION
```

**From your laptop:**
```bash
# If Raspberry Pi is on the same network
nmap -sn 192.168.1.0/24 | grep -B 2 -i raspberry

# Or check your router's admin page for connected devices
```

### Accessing the API from Your Laptop

Once the server is running on the Pi, you can access it from your laptop using the Pi's IP address:

#### Method 1: Using Python Test Client (Easy)

**On your laptop:**
```bash
# Edit test_client.py and set PI_IP to your Raspberry Pi's IP
# Then run:
python3 test_client.py

# Or with a custom query:
python3 test_client.py "What are the symptoms of a common cold?"
```

**Note:** You'll need `requests` installed on your laptop:
```bash
pip install requests
```

#### Method 2: Using curl

**Test from your laptop:**
```bash
# Replace <PI_IP> with your Raspberry Pi's IP address
curl -X POST "http://<PI_IP>:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the symptoms of a common cold?"}'
```

#### Method 3: Using Browser (Interactive API Docs)

**Access API docs from your laptop's browser:**
- Swagger UI: `http://<PI_IP>:8000/docs`
- ReDoc: `http://<PI_IP>:8000/redoc`

**Example:**
If your Raspberry Pi IP is `192.168.1.100`, visit `http://192.168.1.100:8000/docs` in your browser.

## API Endpoints

### Health Check
- **GET** `/`
- Returns service status and model information

### Ask Question
- **POST** `/ask`
- **Request Body:**
  ```json
  {
    "query": "What are the symptoms of a common cold?"
  }
  ```
- **Response:**
  ```json
  {
    "response": "Common symptoms of a cold include..."
  }
  ```

## Testing

Test the API using curl:
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the symptoms of a common cold?"}'
```

Or use the interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Notes

- The `phi3:mini` model is optimized for lightweight inference on resource-constrained devices like Raspberry Pi 5
- Ensure Ollama is running before starting the FastAPI server
- The system prompt instructs the model to provide medical information with appropriate disclaimers
- For production use, consider adding authentication, rate limiting, and logging

## Troubleshooting

**Issue: Connection refused to Ollama**
- Ensure Ollama service is running: `systemctl status ollama` (or check your service manager)
- Verify Ollama is listening on the default port: `netstat -tuln | grep 11434`

**Issue: Model not found**
- Pull the model: `ollama pull phi3:mini`
- Verify: `ollama list`

**Issue: Out of memory**
- The Raspberry Pi 5 with 8GB RAM should handle `phi3:mini` well
- If issues occur, ensure no other memory-intensive processes are running
- Consider using `phi3:mini-instruct` variant if available

**Issue: pydantic-core build failure (Rust compilation error)**
- This error typically occurs when pydantic-core needs to be built from source (e.g., Python 3.13 or missing pre-built wheels)
- Solutions:
  1. **Recommended**: Use Python 3.11 or 3.12 which have pre-built wheels for ARM64:
     ```bash
     # Check Python version
     python3 --version
     
     # If using Python 3.13, consider using Python 3.12 instead
     # Install Python 3.12 if needed (on Raspberry Pi OS):
     sudo apt update && sudo apt install python3.12 python3.12-venv
     python3.12 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
  2. **Alternative**: Install Rust to allow building from source:
     ```bash
     curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
     source ~/.cargo/env
     pip install -r requirements.txt
     ```
  3. **Alternative**: Try installing pydantic without building from source:
     ```bash
     pip install --only-binary :all: -r requirements.txt
     ```

