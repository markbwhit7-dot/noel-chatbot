# Noel Whittaker Financial Chatbot

A RAG-based chatbot for financial education, powered by content from Noel Whittaker's "Super Made Simple" book.

## Features

- **Conversational AI** - Ask questions about superannuation, investing, and personal finance
- **Source Citations** - Every response includes chapter and page references
- **Free to Run** - Uses Groq (free tier) for LLM and local embeddings

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│  Qdrant Cloud   │
│   :5173         │     │   :8000         │     │  (vectors)      │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Groq API      │
                        │   (Llama 3.1)   │
                        └─────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React, Vite, TypeScript |
| Backend | FastAPI, LlamaIndex |
| Vector DB | Qdrant Cloud |
| LLM | Groq (Llama 3.1 8B) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/markbwhit7-dot/noel-chatbot.git
cd noel-chatbot
```

### 2. Set up the backend

```bash
cd backend

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key
DEBUG=true
EOF

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload
```

### 3. Set up the frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 4. Open the app

Visit http://localhost:5173

## PDF Processing Scripts

The `scripts/` folder contains utilities for processing PDF content:

```bash
# Split PDF into chapters
python scripts/split_pdf.py

# Chunk chapters with metadata
python scripts/chunk_chapters.py

# Ingest into Qdrant
python scripts/ingest_to_qdrant.py
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat/` | POST | Send a message and get a response |
| `/api/chat/history/{id}` | GET | Get conversation history |
| `/health` | GET | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "How does salary sacrifice work?"}'
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | Groq API key for LLM |
| `QDRANT_URL` | No | Qdrant instance URL (has default) |
| `QDRANT_API_KEY` | No | Qdrant API key (has default) |
| `SUPABASE_URL` | No | Supabase URL (optional, for history) |
| `SUPABASE_KEY` | No | Supabase key (optional) |

## Getting API Keys

- **Groq** (free): https://console.groq.com
- **Qdrant Cloud** (free tier): https://cloud.qdrant.io

## License

For educational purposes only. Content from "Super Made Simple" by Noel Whittaker.

## Disclaimer

This chatbot is for educational purposes only. Always consult a licensed financial advisor for personal financial advice.
