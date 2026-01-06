"""
Main FastAPI application for the PDF Hint Chatbot.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
import os

from .config import settings
from .models import (
    ChatRequest,
    ChatResponse,
    Message,
    HealthResponse,
    ClearResponse,
    ErrorResponse,
    SessionInfo,
)
from .services.knowledge_base import KnowledgeBase
from .services.llm_service import LLMService
from .services.chat_manager import ChatManager


# Initialize FastAPI app
app = FastAPI(
    title="PDF Hint Chatbot",
    description="Educational chatbot that provides hints based on class materials",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances (initialized on startup)
knowledge_base: KnowledgeBase = None
chat_manager: ChatManager = None
llm_service: LLMService = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    global knowledge_base, chat_manager, llm_service

    print("\n" + "=" * 70)
    print("PDF HINT CHATBOT - STARTING UP")
    print("=" * 70)

    # Initialize knowledge base
    print("\n[1/3] Initializing Knowledge Base...")
    knowledge_base = KnowledgeBase(str(settings.DATA_DIR))
    knowledge_base.load_pdfs()

    # Check if any PDFs were loaded
    if not knowledge_base.has_content():
        print("\n⚠️  WARNING: No PDFs were loaded!")
        print("   Please add PDF files to:")
        print(f"   - {settings.PDF_MATERIALS_DIR}")
        print(f"   - {settings.PDF_ASSIGNMENTS_DIR}")
        print("   The chatbot will have no knowledge to work with.")

    # Initialize chat manager
    print(f"\n[2/3] Initializing Chat Manager...")
    chat_manager = ChatManager(
        max_history_length=settings.MAX_HISTORY_LENGTH,
        session_timeout_minutes=settings.SESSION_TIMEOUT_MINUTES,
    )

    # Initialize LLM service (RAG approach - no initial context needed)
    print(f"\n[3/3] Initializing LLM Service...")
    try:
        llm_service = LLMService(
            api_key=settings.GEMINI_API_KEY,
            model_name=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
            max_output_tokens=settings.MAX_OUTPUT_TOKENS,
            top_p=settings.TOP_P,
            top_k=settings.TOP_K,
        )
        print("✓ LLM Service configured successfully")
        print("✓ Using RAG (Retrieval-Augmented Generation) with ChromaDB")
    except Exception as e:
        print(f"✗ ERROR initializing LLM Service: {str(e)}")
        print("   Please check your GEMINI_API_KEY in the .env file")

    print("\n" + "=" * 70)
    print("✓ APPLICATION READY")
    print("=" * 70)
    print(f"Server running at: http://{settings.HOST}:{settings.PORT}")
    print("Open your browser to start chatting!")
    print("=" * 70 + "\n")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - send a message and receive a hint-based response.

    Args:
        request: ChatRequest with optional session_id and message

    Returns:
        ChatResponse with session_id, response, and timestamp
    """
    # Check if LLM service is initialized
    if llm_service is None:
        raise HTTPException(
            status_code=500,
            detail="LLM service not initialized. Please check API key configuration.",
        )

    # Create or validate session
    if not request.session_id or not chat_manager.session_exists(request.session_id):
        session_id = chat_manager.create_session()
    else:
        # Check if session is expired
        if chat_manager.is_session_expired(request.session_id):
            # Create new session for expired one
            session_id = chat_manager.create_session()
        else:
            session_id = request.session_id

    try:
        # Add user message to history
        chat_manager.add_message(session_id, "user", request.message)

        # Get conversation history (excluding the just-added message)
        history = chat_manager.get_history(session_id)
        context_history = history[:-1] if len(history) > 1 else []

        # Retrieve relevant context using semantic search (RAG)
        relevant_context = knowledge_base.get_relevant_context(
            query=request.message,
            n_results=5  # Get top 5 most relevant chunks
        )

        # Generate hint-based response with retrieved context
        response = llm_service.generate_hint(
            question=request.message,
            relevant_context=relevant_context,
            conversation_history=context_history
        )

        # Add assistant response to history
        chat_manager.add_message(session_id, "assistant", response)

        return ChatResponse(
            session_id=session_id,
            response=response,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        # Log error
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/api/history/{session_id}", response_model=List[Message])
async def get_history(session_id: str):
    """
    Get conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        List of messages in the conversation
    """
    try:
        history = chat_manager.get_history(session_id)
        return history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/clear/{session_id}", response_model=ClearResponse)
async def clear_history(session_id: str):
    """
    Clear conversation history for a session.

    Args:
        session_id: Session identifier

    Returns:
        Success message
    """
    try:
        chat_manager.clear_session(session_id)
        return ClearResponse(
            message="History cleared successfully", session_id=session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/session/{session_id}", response_model=SessionInfo)
async def get_session_info(session_id: str):
    """
    Get information about a session.

    Args:
        session_id: Session identifier

    Returns:
        SessionInfo with details about the session
    """
    info = chat_manager.get_session_info(session_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionInfo(**info)


@app.post("/api/cleanup")
async def cleanup_sessions():
    """
    Manually trigger cleanup of expired sessions.

    Returns:
        Number of sessions cleaned up
    """
    count = chat_manager.cleanup_expired_sessions()
    return {"cleaned_up": count, "message": f"Cleaned up {count} expired session(s)"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Service health status and loaded PDF count
    """
    summary = knowledge_base.get_summary()
    return HealthResponse(
        status="healthy",
        materials_loaded=summary["materials_count"],
        assignments_loaded=summary["assignments_count"],
        total_pdfs=summary["total_pdfs"],
        has_content=knowledge_base.has_content(),
    )


@app.get("/api/stats")
async def get_stats():
    """
    Get statistics about the application.

    Returns:
        Application statistics
    """
    kb_summary = knowledge_base.get_summary()
    chat_stats = chat_manager.get_stats()

    return {
        "knowledge_base": kb_summary,
        "chat_sessions": chat_stats,
    }


@app.get("/api/assignment-questions")
async def get_assignment_questions():
    """
    Get all structured assignment questions for sidebar display.

    Returns:
        List of assignment questions with metadata
    """
    questions_by_file = []

    for filename, structured_content in knowledge_base.assignment_structures.items():
        questions = structured_content.get('questions', [])

        if questions:
            questions_by_file.append({
                "filename": filename,
                "questions": [
                    {
                        "id": q['id'],
                        "text": q['text'],
                        "has_scenario": q.get('has_scenario', False),
                        "has_table": q.get('has_table', False),
                        "has_image": q.get('has_image', False),
                    }
                    for q in questions
                ]
            })

    return {"assignments": questions_by_file}


# Mount static files (frontend)
if os.path.exists(str(settings.STATIC_DIR)):
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = settings.STATIC_DIR / "index.html"
    if os.path.exists(index_path):
        return FileResponse(str(index_path))
    else:
        return {
            "message": "PDF Hint Chatbot API",
            "docs": "/docs",
            "health": "/health",
        }


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
