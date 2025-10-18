"""
AI Interviewer FastAPI Application
Main entry point for the WebRTC-based AI interviewer
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from aiortc import RTCSessionDescription
from dotenv import load_dotenv

from app.webrtc_handler import get_webrtc_handler
from app.stt import get_stt_handler
from app.llm import get_llm_handler
from app.tts import get_tts_handler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    logger.info("Starting AI Interviewer application...")
    
    # Initialize handlers on startup
    try:
        stt = get_stt_handler()
        await stt.initialize()
        logger.info("STT handler initialized")
        
        tts = get_tts_handler()
        await tts.initialize()
        logger.info("TTS handler initialized")
        
        # LLM handler initializes lazily
        llm = get_llm_handler()
        logger.info("LLM handler ready")
        
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down AI Interviewer application...")
    webrtc = get_webrtc_handler()
    await webrtc.cleanup()


# Create FastAPI app
app = FastAPI(
    title="AI Interviewer",
    description="WebRTC-based AI interviewing system with speech recognition and synthesis",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class OfferRequest(BaseModel):
    sdp: str
    type: str


class AnswerResponse(BaseModel):
    sdp: str
    type: str
    peer_id: str


# Routes
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main page"""
    try:
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>AI Interviewer</h1><p>Frontend not found. Please create index.html</p>",
            status_code=404
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Interviewer",
        "version": "1.0.0"
    }


@app.post("/offer", response_model=AnswerResponse)
async def offer(request: OfferRequest):
    """
    Handle WebRTC offer from client
    Creates peer connection and returns SDP answer
    """
    try:
        logger.info("Received WebRTC offer")
        
        # Get WebRTC handler
        webrtc = get_webrtc_handler()
        
        # Create new peer connection
        peer_id, pc = webrtc.create_peer_connection()
        
        # Set remote description (offer from client)
        offer_sdp = RTCSessionDescription(sdp=request.sdp, type=request.type)
        await pc.setRemoteDescription(offer_sdp)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        logger.info(f"Created answer for peer: {peer_id}")
        
        return AnswerResponse(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type,
            peer_id=peer_id
        )
        
    except Exception as e:
        logger.error(f"Error handling offer: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/reset/{peer_id}")
async def reset_conversation(peer_id: str):
    """Reset conversation history for a peer"""
    try:
        llm = get_llm_handler()
        llm.reset_conversation()
        logger.info(f"Reset conversation for peer: {peer_id}")
        return {"status": "success", "message": "Conversation reset"}
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/conversation/{peer_id}")
async def get_conversation(peer_id: str):
    """Get conversation history for a peer"""
    try:
        llm = get_llm_handler()
        history = llm.get_conversation_context()
        return {
            "peer_id": peer_id,
            "conversation": history
        }
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.delete("/peer/{peer_id}")
async def close_peer(peer_id: str):
    """Close a specific peer connection"""
    try:
        webrtc = get_webrtc_handler()
        await webrtc.close_peer_connection(peer_id)
        return {"status": "success", "message": f"Peer {peer_id} closed"}
    except Exception as e:
        logger.error(f"Error closing peer: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# Run with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
