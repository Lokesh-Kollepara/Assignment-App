"""
Pydantic models for API request and response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    session_id: Optional[str] = Field(
        None,
        description="Session ID for continuing a conversation. If not provided, a new session will be created.",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The student's question or message",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Can you help me understand question 3 from the assignment?",
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    session_id: str = Field(..., description="Session ID for this conversation")
    response: str = Field(..., description="Hint-based response from the assistant")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the response")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "response": "Question 3 relates to the concept discussed in the lecture about algorithms. Try reviewing that section and think about how recursion applies here. What's the base case?",
                "timestamp": "2024-01-15T10:30:00.000000",
            }
        }


class Message(BaseModel):
    """Model for a single chat message."""

    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the message")

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "How do I solve problem 5?",
                "timestamp": "2024-01-15T10:30:00.000000",
            }
        }


class SessionInfo(BaseModel):
    """Model for session information."""

    session_id: str = Field(..., description="Session identifier")
    message_count: int = Field(..., description="Number of messages in the session")
    created_at: str = Field(..., description="ISO 8601 timestamp when session was created")
    last_activity: str = Field(..., description="ISO 8601 timestamp of last activity")
    is_expired: bool = Field(..., description="Whether the session has expired")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_count": 8,
                "created_at": "2024-01-15T10:00:00.000000",
                "last_activity": "2024-01-15T10:30:00.000000",
                "is_expired": False,
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Service status")
    materials_loaded: int = Field(..., description="Number of class material PDFs loaded")
    assignments_loaded: int = Field(..., description="Number of assignment PDFs loaded")
    total_pdfs: int = Field(..., description="Total number of PDFs loaded")
    has_content: bool = Field(
        ..., description="Whether any PDFs have been successfully loaded"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "materials_loaded": 5,
                "assignments_loaded": 3,
                "total_pdfs": 8,
                "has_content": True,
            }
        }


class ErrorResponse(BaseModel):
    """Response model for error messages."""

    detail: str = Field(..., description="Error message")

    class Config:
        json_schema_extra = {"example": {"detail": "Session not found"}}


class ClearResponse(BaseModel):
    """Response model for clear history endpoint."""

    message: str = Field(..., description="Success message")
    session_id: str = Field(..., description="Session ID that was cleared")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "History cleared successfully",
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
