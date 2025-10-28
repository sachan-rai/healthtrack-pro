# HealthTrack Pro

## Development Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Git

### Quick Start
1. Clone the repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy environment file: `cp env.example .env`
6. Add your OpenAI API key to `.env`
7. Build the index: `python -m app.ingest.build_index`
8. Start the server: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
9. Open http://localhost:8000

## Project Structure
- `app/` - Main application code
- `app/data/` - Recipe database and knowledge base
- `app/rag/` - RAG pipeline for AI recommendations
- `app/ingest/` - Data ingestion and indexing
- `index.html` - Web interface

## Features
- 70+ healthy recipes across multiple diets
- AI-powered meal and workout planning
- Evidence-based recommendations
- Responsive web interface
