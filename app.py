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
    
    # Pre-warm model to improve first request response time
    def warm_up_model():
        """Pre-load the model into memory"""
        try:
            ollama.chat(
                model='phi3:mini',
                messages=[{'role': 'user', 'content': 'test'}],
                options={'num_predict': 5, 'num_ctx': 128}  # Minimal tokens for warm-up
            )
            print("✅ Model warmed up and ready")
        except Exception as e:
            print(f"⚠️  Model warm-up failed: {e}")
    
    warm_up_model()
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

# Safety filtering patterns - compiled for performance
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

# Compile regex patterns once for better performance
DANGEROUS_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_KEYWORDS]
UNCERTAINTY_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in UNCERTAINTY_INDICATORS]

DISCLAIMER = "⚠️ Disclaimer: Not a substitute for professional advice."

def check_dangerous_content(text: str) -> bool:
    """Check if response contains dangerous medical keywords"""
    text_lower = text.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(text_lower):
            return True
    return False

def check_uncertain_content(text: str) -> bool:
    """Check if response contains uncertainty indicators"""
    text_lower = text.lower()
    for pattern in UNCERTAINTY_PATTERNS:
        if pattern.search(text_lower):
            return True
    return False

# Compile regex patterns for parsing (better performance)
DIAGNOSIS_PATTERNS = [
    re.compile(r'(?:diagnosis/assessment|diagnosis)[:\s]+(.+?)(?=\n\s*(?:advice|recommendation)|$)', re.IGNORECASE | re.DOTALL | re.MULTILINE),
    re.compile(r'(?:diagnosis/assessment|diagnosis)[:\s]+(.+?)(?=\n\s*\n|$)', re.IGNORECASE | re.DOTALL | re.MULTILINE),
    re.compile(r'^(?:diagnosis/assessment|diagnosis)[:\s]+(.+?)(?=\n|$)', re.IGNORECASE | re.DOTALL | re.MULTILINE),
]

ADVICE_PATTERNS = [
    re.compile(r'(?:advice/recommendations?|advice)[:\s]+(.+?)$', re.IGNORECASE | re.DOTALL | re.MULTILINE),
    re.compile(r'(?:advice/recommendations?|advice)[:\s]+(.+)', re.IGNORECASE | re.DOTALL | re.MULTILINE),
]

# Compiled cleanup patterns
CLEANUP_SEPARATORS = re.compile(r'\s*-\s*(?:Diagnosis/Assessment|Advice/Recommendations):\s*', re.IGNORECASE)
CLEANUP_DASHES = re.compile(r'\s*[-–—]\s*')
CLEANUP_TRAILING_DASH = re.compile(r'\s*[-–—]\s*$')
CLEANUP_EXTRA_LABELS_DIAG = re.compile(r'\s*(?:advice|recommendation).*$', re.IGNORECASE)
CLEANUP_EXTRA_LABELS_ADV = re.compile(r'\s*(?:confidence|note).*$', re.IGNORECASE)
CLEANUP_WHITESPACE = re.compile(r'\s+')
CLEANUP_DIAGNOSIS_PREFIX = re.compile(r'^\s*(?:diagnosis|assessment|⚠️\s*Disclaimer)[:\s]*', re.IGNORECASE)
CLEANUP_ADVICE_PREFIX = re.compile(r'^\s*(?:advice|recommendation)[:\s]*', re.IGNORECASE)

def parse_structured_response(response_text: str) -> dict:
    """
    Parse the model response into structured format.
    Attempts to extract diagnosis and advice from the response.
    Uses compiled regex patterns for better performance.
    """
    # Remove disclaimer if already present
    response_text = response_text.replace(DISCLAIMER, "").strip()
    
    # Clean up common separator patterns
    response_text = CLEANUP_SEPARATORS.sub('\n', response_text)
    response_text = CLEANUP_DASHES.sub('\n', response_text)
    
    # Try to extract structured fields from response
    diagnosis = ""
    advice = ""
    
    # Try to extract diagnosis using compiled patterns
    for pattern in DIAGNOSIS_PATTERNS:
        match = pattern.search(response_text)
        if match:
            diagnosis = match.group(1).strip()
            # Clean up: remove any trailing separators, extra labels, or continuation markers
            diagnosis = CLEANUP_TRAILING_DASH.sub('', diagnosis)
            diagnosis = CLEANUP_EXTRA_LABELS_DIAG.sub('', diagnosis)
            diagnosis = CLEANUP_WHITESPACE.sub(' ', diagnosis)  # Normalize whitespace
            if diagnosis and len(diagnosis) > 10:  # Valid diagnosis found
                break
    
    # Try to extract advice using compiled patterns
    for pattern in ADVICE_PATTERNS:
        match = pattern.search(response_text)
        if match:
            advice = match.group(1).strip()
            # Clean up: remove any trailing markers
            advice = CLEANUP_TRAILING_DASH.sub('', advice)
            advice = CLEANUP_EXTRA_LABELS_ADV.sub('', advice)
            advice = CLEANUP_WHITESPACE.sub(' ', advice)  # Normalize whitespace
            if advice and len(advice) > 10:  # Valid advice found
                break
    
    # If extraction failed, try intelligent splitting
    if not diagnosis or not advice:
        # Remove all label markers first (compiled pattern)
        label_remover = re.compile(r'(?:diagnosis/assessment|diagnosis|advice/recommendations?|advice)[:\s]*', re.IGNORECASE)
        cleaned = label_remover.sub('', response_text)
        
        # Try splitting by double newlines or clear separators
        split_pattern = re.compile(r'\n\n+|(?:\n|^)\s*(?:Advice|Recommendation)', re.IGNORECASE | re.MULTILINE)
        parts = [p.strip() for p in split_pattern.split(cleaned) if p.strip()]
        
        if len(parts) >= 2:
            diagnosis = parts[0].strip()
            advice = ' '.join(parts[1:]).strip()
        elif len(parts) == 1:
            # Single part - split roughly in half
            text = parts[0]
            split_point = len(text) // 2
            # Try to split at sentence boundary
            sentence_end = max(
                text.rfind('.', 0, split_point),
                text.rfind('!', 0, split_point),
                text.rfind('?', 0, split_point)
            )
            if sentence_end > len(text) * 0.3:  # Only use if reasonable split point
                split_point = sentence_end + 1
            
            diagnosis = text[:split_point].strip()
            advice = text[split_point:].strip()
    
    # Final cleanup - remove any remaining label text (using compiled patterns)
    diagnosis = CLEANUP_DIAGNOSIS_PREFIX.sub('', diagnosis)
    advice = CLEANUP_ADVICE_PREFIX.sub('', advice)
    
    # Remove any remaining separator markers
    diagnosis = CLEANUP_TRAILING_DASH.sub('', diagnosis).strip()
    advice = CLEANUP_TRAILING_DASH.sub('', advice).strip()
    
    # Fallback if still empty
    if not diagnosis or len(diagnosis) < 10:
        # Use full response text as diagnosis (no truncation)
        diagnosis = response_text.strip()
        # Remove any labels from the beginning
        diagnosis = CLEANUP_DIAGNOSIS_PREFIX.sub('', diagnosis)
        diagnosis = CLEANUP_DASHES.sub(' ', diagnosis)
    
    if not advice or len(advice) < 10:
        # Try to find advice after diagnosis
        remaining = response_text[len(diagnosis):].strip() if len(response_text) > len(diagnosis) else response_text.strip()
        advice = remaining if remaining else "Please consult a healthcare professional for proper evaluation."
        # Remove any labels
        advice = CLEANUP_ADVICE_PREFIX.sub('', advice)
        advice = CLEANUP_DASHES.sub(' ', advice)
    
    # Final normalization - remove extra whitespace
    diagnosis = CLEANUP_WHITESPACE.sub(' ', diagnosis).strip()
    advice = CLEANUP_WHITESPACE.sub(' ', advice).strip()
    
    return {
        "diagnosis": diagnosis,  # No character limit - show full response
        "advice": advice  # No character limit - show full response
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
    
    Returns structured output with diagnosis and advice.
    Includes safety filtering to prevent dangerous medical claims.
    Optimized for fast response times with compiled regex patterns.
    
    Args:
        request: QueryRequest containing the user's query string
        
    Returns:
        QueryResponse with structured medical information (diagnosis, advice)
        
    Raises:
        HTTPException: If the query is empty or Ollama connection fails
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    try:
        # Optimized shorter prompt for faster processing
        structured_prompt = f"""Brief medical assessment. Format:
- Diagnosis/Assessment: [assessment]
- Advice/Recommendations: [advice]

Query: {request.query}"""
        
        # Call Ollama API with phi3:mini model (removed redundant health check)
        try:
            response = ollama.chat(
                model='phi3:mini',
                messages=[
                    {
                        'role': 'system',
                        'content': 'Medical assistant. Brief, structured responses. Not medical advice.'
                    },
                    {
                        'role': 'user',
                        'content': structured_prompt
                    }
                ],
                options={
                    'temperature': 0.7,      # Lower temperature for focused responses
                    'num_ctx': 512,          # Reduced context window (default 2048)
                    'num_thread': 4,         # Optimize for Raspberry Pi 5
                    'repeat_penalty': 1.1,   # Prevent repetition, faster completion
                    'top_p': 0.9,            # Nucleus sampling for faster generation
                    'top_k': 20,            # Limit vocabulary for speed
                }
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
        
        # Don't add disclaimer to diagnosis - footer disclaimer is sufficient
        
        return QueryResponse(**structured)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query with Ollama: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

