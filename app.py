"""
FastAPI backend for AI Medical Assistant
Connects to local Ollama installation running phi3:mini model
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import ollama

# Initialize FastAPI app
app = FastAPI(
    title="AI Medical Assistant",
    description="Local AI medical assistant powered by Ollama phi3:mini",
    version="1.0.0"
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# Health check endpoint
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Medical Assistant",
        "model": "phi3:mini"
    }

# Main query endpoint
@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Process a medical query using the local Ollama phi3:mini model
    
    Args:
        request: QueryRequest containing the user's query string
        
    Returns:
        QueryResponse with the model's reply
        
    Raises:
        HTTPException: If the query is empty or Ollama connection fails
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Call Ollama API with phi3:mini model
        response = ollama.chat(
            model='phi3:mini',
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a helpful medical assistant. Provide clear, concise, and accurate medical information. Always remind users to consult with healthcare professionals for serious concerns.'
                },
                {
                    'role': 'user',
                    'content': request.query
                }
            ]
        )
        
        # Extract the response text
        reply = response['message']['content']
        
        return QueryResponse(response=reply)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query with Ollama: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

