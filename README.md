# AI Medical Assistant - Raspberry Pi 5

A lightweight AI medical assistant backend running locally on Raspberry Pi 5 using Ollama and FastAPI.

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

## Running the Server

**Launch the backend server:**
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

The server will be available at:
- Local access: `http://localhost:8000`
- Network access: `http://<raspberry-pi-ip>:8000`

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

