"""
Application launcher script for the PDF Hint Chatbot.
"""
import uvicorn
from app.config import settings


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Starting PDF Hint Chatbot Server...")
    print("=" * 70 + "\n")

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
