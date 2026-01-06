# PDF Hint Chatbot

An educational chatbot that provides **hints** (not direct answers) based on class materials and assignments stored in PDF files. Built with FastAPI, Gemini Flash 2.0, and vanilla JavaScript.

## Features

- **Hint-Based Learning**: Chatbot provides educational hints instead of direct answers to promote learning
- **PDF Knowledge Base**: Uses class materials and assignments as the sole source of knowledge
- **Conversation Memory**: Maintains chat history in-memory for contextual responses
- **Clean Web Interface**: Simple, responsive chat interface
- **Gemini Flash 2.0**: Powered by Google's latest AI model

## Prerequisites

- Python 3.8 or higher
- Gemini API key (get one at [https://makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey))
- Your class materials and assignment PDFs

## Quick Start

### 1. Clone or Download the Project

```bash
cd /Users/lokeshkollepara/Documents/Assignment-Project
```

### 2. Create a Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Edit the `.env` file and add your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

### 5. Add Your PDF Files

Place your PDF files in the appropriate directories:

- **Class Materials**: `data/pdfs/materials/`
- **Assignments**: `data/pdfs/assignments/`

Example:
```bash
# Copy your PDFs
cp ~/Downloads/lecture_notes.pdf data/pdfs/materials/
cp ~/Downloads/assignment1.pdf data/pdfs/assignments/
```

### 6. Run the Application

```bash
python run.py
```

The server will start at [http://localhost:8000](http://localhost:8000)

### 7. Open Your Browser

Navigate to [http://localhost:8000](http://localhost:8000) and start chatting!

## Project Structure

```
Assignment-Project/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration settings
│   ├── models.py                  # Pydantic models
│   ├── services/
│   │   ├── pdf_processor.py      # PDF text extraction
│   │   ├── llm_service.py        # Gemini API integration
│   │   ├── knowledge_base.py     # PDF content management
│   │   └── chat_manager.py       # Conversation storage
│   └── prompts/
│       └── system_prompts.py     # Hint-based prompts
├── static/
│   ├── index.html                # Chat interface
│   ├── css/style.css             # Styling
│   └── js/chat.js                # Frontend logic
├── data/
│   └── pdfs/
│       ├── materials/            # Place class materials here
│       └── assignments/          # Place assignments here
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── run.py                        # Application launcher
└── README.md                     # This file
```

## API Endpoints

### Chat Endpoint
- **POST** `/api/chat`
  - Send a message and receive a hint-based response
  - Request: `{"session_id": "optional", "message": "your question"}`
  - Response: `{"session_id": "...", "response": "...", "timestamp": "..."}`

### History Endpoint
- **GET** `/api/history/{session_id}`
  - Retrieve conversation history for a session

### Clear History
- **POST** `/api/clear/{session_id}`
  - Clear conversation history for a session

### Health Check
- **GET** `/health`
  - Check service status and loaded PDF count

### API Documentation
- **GET** `/docs`
  - Interactive API documentation (Swagger UI)

## Configuration

Edit `.env` to customize settings:

```env
# API Configuration
GEMINI_API_KEY=your_api_key_here

# Application Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Chat Configuration
MAX_HISTORY_LENGTH=20
SESSION_TIMEOUT_MINUTES=60

# LLM Configuration
TEMPERATURE=0.7
```

## How It Works

1. **PDF Loading**: On startup, the application loads all PDFs from `data/pdfs/materials/` and `data/pdfs/assignments/`
2. **Text Extraction**: PyMuPDF extracts text from each PDF
3. **Knowledge Base**: All PDF content is stored in memory and injected into the LLM's system prompt
4. **Hint Generation**: When you ask a question, the LLM uses ONLY the PDF content to provide hints
5. **Conversation History**: Your chat history is stored in memory for contextual responses

## Usage Tips

### Getting Good Hints

The chatbot is designed to guide you, not give answers. Try:

- "Can you help me understand question 3?"
- "I'm stuck on problem 5, where should I start?"
- "What concept from the materials relates to this assignment?"

### What the Chatbot Does

- ✅ Points to relevant sections in materials
- ✅ Asks guiding questions
- ✅ Breaks down complex problems
- ✅ Suggests concepts to review
- ✅ Provides partial information

### What the Chatbot Doesn't Do

- ❌ Give direct answers
- ❌ Solve problems for you
- ❌ Use external knowledge (only your PDFs)
- ❌ Complete assignments for you

## Troubleshooting

### Error: "GEMINI_API_KEY not set"

Make sure you've added your API key to the `.env` file:
```env
GEMINI_API_KEY=your_actual_key_here
```

### No PDFs Loaded

Check that:
1. PDF files are in `data/pdfs/materials/` or `data/pdfs/assignments/`
2. Files have `.pdf` extension
3. PDFs are not corrupted or password-protected

### "I don't have information about that"

This means your question is outside the scope of the loaded PDFs. The chatbot can only answer questions based on the materials you've provided.

### Port Already in Use

If port 8000 is taken, change it in `.env`:
```env
PORT=8001
```

## Development

### Running in Debug Mode

Enable auto-reload for development:

```env
DEBUG=True
```

Then run:
```bash
python run.py
```

### Testing API Endpoints

Use the interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs)

### Adding New Features

The codebase is modular:
- PDF processing: `app/services/pdf_processor.py`
- LLM logic: `app/services/llm_service.py`
- Prompts: `app/prompts/system_prompts.py`
- Frontend: `static/`

## Limitations

- **In-Memory Storage**: Conversation history is lost when the server restarts
- **Single Instance**: Not designed for multi-server deployment
- **PDF Quality**: Scanned PDFs or complex layouts may not extract well
- **Context Window**: Very large PDF collections may exceed the model's context limit
- **No Authentication**: No user management or access control

## Future Enhancements

Potential improvements:
- Persistent storage (PostgreSQL/Redis)
- Vector embeddings for better context retrieval
- PDF upload via web interface
- User authentication
- Multi-user support
- Better PDF preprocessing (OCR for scanned documents)

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review server logs for error messages
3. Verify your PDF files are readable
4. Test with a simple question to ensure the system works

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Google Gemini](https://ai.google.dev/) - LLM API
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Pydantic](https://docs.pydantic.dev/) - Data validation

---

**Happy Learning!** Remember, the goal is to understand concepts, not just get answers. Use the hints wisely!
