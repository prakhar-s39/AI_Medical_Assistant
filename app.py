"""
FastAPI backend for AI Medical Assistant
Connects to local Ollama installation running phi3:mini model
"""

import re
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import ollama
import os

# Check Ollama connection on startup
def check_ollama_connection():
    """Verify Ollama is accessible and model is available"""
    try:
        # Check if Ollama is running
        models = ollama.list()
        model_names = [model['name'] for model in models.get('models', [])]
        
        # Check if phi3:mini is available
        if 'phi3:mini' not in model_names:
            print("⚠️  Warning: phi3:mini model not found. Available models:", model_names)
            print("   Run: ollama pull phi3:mini")
            return False, "Model 'phi3:mini' not found"
        
        return True, "Ollama connected successfully"
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("   Make sure Ollama is running: systemctl status ollama")
        return False, str(e)

# Check Ollama on startup
ollama_available, ollama_status = check_ollama_connection()
if ollama_available:
    print("✅ Ollama connection verified")
else:
    print(f"⚠️  Ollama check failed: {ollama_status}")

# Initialize FastAPI app
app = FastAPI(
    title="AI Medical Assistant",
    description="Local AI medical assistant powered by Ollama phi3:mini with safety filtering",
    version="2.0.0"
)

# Mount static files for frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    
    @app.get("/")
    async def read_root():
        """Serve the frontend index.html"""
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    # Fallback root endpoint if frontend doesn't exist
    @app.get("/")
    async def read_root():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": "AI Medical Assistant",
            "model": "phi3:mini",
            "version": "2.0.0",
            "features": ["structured_output", "safety_filtering"],
            "frontend": "not_found"
        }

# Request/Response models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    diagnosis: str = Field(description="Medical diagnosis or assessment")
    advice: str = Field(description="Advice or recommendations")
    confidence: str = Field(description="Confidence level (e.g., 'low', 'medium', 'high')")

# Safety filtering patterns
DANGEROUS_KEYWORDS = [
    r'\b(prescribe|prescription)\b',
    r'\b(dose|dosage)\s+\d+',
    r'\b(take|ingest)\s+\d+',
    r'\b(specific\s+)?medication\b',
    r'\bdefinitely\s+(have|diagnosed)\b',
    r'\bguarantee|guaranteed\b',
]

UNCERTAINTY_INDICATORS = [
    r'\b(maybe|perhaps|might|could|possibly|uncertain|unclear)\b',
    r'\b(not\s+sure|don\'t\s+know|hard\s+to\s+tell)\b',
    r'\b(suggests|indicates|may|could\s+be)\b',
]

DISCLAIMER = "⚠️ Disclaimer: Not a substitute for professional advice."

def check_dangerous_content(text: str) -> bool:
    """Check if response contains dangerous medical keywords"""
    text_lower = text.lower()
    for pattern in DANGEROUS_KEYWORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def check_uncertain_content(text: str) -> bool:
    """Check if response contains uncertainty indicators"""
    text_lower = text.lower()
    for pattern in UNCERTAINTY_INDICATORS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

def parse_structured_response(response_text: str) -> dict:
    """
    Parse the model response into structured format.
    Attempts to extract diagnosis, advice, and confidence from the response.
    """
    # Remove disclaimer if already present
    response_text = response_text.replace(DISCLAIMER, "").strip()
    
    # Try to extract structured fields from response
    diagnosis = ""
    advice = ""
    confidence = "medium"
    
    # Look for explicit labels
    diagnosis_match = re.search(r'(?:diagnosis|assessment):\s*(.+?)(?:\n|$|advice|confidence)', response_text, re.IGNORECASE | re.DOTALL)
    advice_match = re.search(r'(?:advice|recommendation):\s*(.+?)(?:\n|$|confidence)', response_text, re.IGNORECASE | re.DOTALL)
    confidence_match = re.search(r'(?:confidence):\s*(low|medium|high)', response_text, re.IGNORECASE)
    
    if diagnosis_match:
        diagnosis = diagnosis_match.group(1).strip()
    if advice_match:
        advice = advice_match.group(1).strip()
    if confidence_match:
        confidence = confidence_match.group(1).lower()
    
    # If no explicit structure found, split intelligently
    if not diagnosis or not advice:
        # Try splitting by common separators
        parts = re.split(r'\n\n+|\n(?:Note:|Important:|Warning:)', response_text)
        if len(parts) >= 2:
            diagnosis = parts[0].strip()
            advice = ' '.join(parts[1:]).strip()
        else:
            # If single block, use first 40% as diagnosis, rest as advice
            split_point = len(response_text) // 2.5
            diagnosis = response_text[:int(split_point)].strip()
            advice = response_text[int(split_point):].strip()
    
    # Fallback if still empty
    if not diagnosis:
        diagnosis = response_text[:200].strip() if response_text else "Unable to assess"
    if not advice:
        advice = response_text[200:].strip() if len(response_text) > 200 else "Please consult a healthcare professional"
    
    # Assess confidence based on content
    if check_uncertain_content(response_text):
        confidence = "low"
    elif re.search(r'\b(typically|usually|often|common)\b', response_text, re.IGNORECASE):
        confidence = "medium"
    elif re.search(r'\b(clear|definite|certain)\b', response_text, re.IGNORECASE):
        confidence = "high"
    
    return {
        "diagnosis": diagnosis[:500],  # Limit length
        "advice": advice[:500],  # Limit length
        "confidence": confidence
    }

# Health check endpoint (API endpoint, separate from root)
@app.get("/api/health")
async def health():
    """Health check endpoint with Ollama status"""
    try:
        # Check Ollama availability
        models = ollama.list()
        model_names = [model['name'] for model in models.get('models', [])]
        has_model = 'phi3:mini' in model_names
        
        return {
            "status": "healthy",
            "service": "AI Medical Assistant",
            "model": "phi3:mini",
            "version": "2.0.0",
            "features": ["structured_output", "safety_filtering"],
            "ollama": {
                "connected": True,
                "model_available": has_model,
                "available_models": model_names
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "service": "AI Medical Assistant",
            "model": "phi3:mini",
            "version": "2.0.0",
            "features": ["structured_output", "safety_filtering"],
            "ollama": {
                "connected": False,
                "error": str(e)
            },
            "warning": "Ollama is not accessible. API will not function properly."
        }

# Main query endpoint
@app.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Process a medical query using the local Ollama phi3:mini model
    
    Returns structured output with diagnosis, advice, and confidence level.
    Includes safety filtering to prevent dangerous medical claims.
    
    Args:
        request: QueryRequest containing the user's query string
        
    Returns:
        QueryResponse with structured medical information
        
    Raises:
        HTTPException: If the query is empty or Ollama connection fails
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Enhanced prompt to encourage structured output
        structured_prompt = f"""Please provide a medical assessment for the following query. Format your response clearly with:
- Diagnosis/Assessment: [your assessment]
- Advice/Recommendations: [your advice]
- Confidence: [low/medium/high]

Remember: Always emphasize consulting healthcare professionals for serious concerns. Do not prescribe medications or specific dosages.

Query: {request.query}"""
        
        # Verify Ollama is accessible before making the call
        try:
            # Quick check - verify Ollama is responding
            ollama.list()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Ollama service is not available. Please ensure Ollama is running: {str(e)}. Try: systemctl status ollama"
            )
        
        # Call Ollama API with phi3:mini model
        try:
            response = ollama.chat(
                model='phi3:mini',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a helpful medical assistant. Provide clear, structured medical information. Always remind users that your advice is not a substitute for professional medical consultation. Never prescribe medications or specific dosages.'
                    },
                    {
                        'role': 'user',
                        'content': structured_prompt
                    }
                ]
            )
        except Exception as e:
            # Check if it's a model not found error
            if 'model' in str(e).lower() or 'not found' in str(e).lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"Model 'phi3:mini' not found. Please run: ollama pull phi3:mini"
                )
            raise HTTPException(
                status_code=503,
                detail=f"Error calling Ollama: {str(e)}"
            )
        
        # Extract the response text
        reply = response['message']['content']
        
        # Apply safety filtering
        needs_disclaimer = check_uncertain_content(reply)
        has_dangerous_content = check_dangerous_content(reply)
        
        # Filter out dangerous keywords by replacing with safer alternatives
        if has_dangerous_content:
            # Replace prescription mentions
            reply = re.sub(r'\b(prescribe|prescription)\b', 'consult a doctor about', reply, flags=re.IGNORECASE)
            # Replace specific dosages
            reply = re.sub(r'\b(dose|dosage)\s+\d+', 'appropriate treatment', reply, flags=re.IGNORECASE)
        
        # Parse into structured format
        structured = parse_structured_response(reply)
        
        # Add disclaimer to diagnosis if uncertain or dangerous content detected
        if needs_disclaimer or has_dangerous_content:
            if not structured["diagnosis"].startswith(DISCLAIMER):
                structured["diagnosis"] = f"{DISCLAIMER} {structured['diagnosis']}"
        
        return QueryResponse(**structured)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query with Ollama: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

