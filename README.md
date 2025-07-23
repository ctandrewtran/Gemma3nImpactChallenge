# Gemma3nImpactChallenge

A hyper-local Retrieval-Augmented Generation (RAG) system for edge devices, powered by Gemma 3n via Ollama, with an intuitive Dash UI, web scraping/indexing, and agentic RAG pipeline.

## Features
- Intuitive Dash UI with admin panel and chat interface
- Admin panel for URL input, refresh, and scheduling
- Web scraper and Milvus-based search index
- Local embeddings via Ollama
- Agentic RAG pipeline (translation, search, evaluation, response)
- Local session DB (SQLite)
- Easy local install and setup

## Project Structure
```
Gemma3nImpactChallenge/
│
├── app.py                  # Dash app entry point
├── requirements.txt
├── README.md
│
├── rag/
│   ├── agents.py           # RAG pipeline logic
│   ├── scrape.py           # Web scraping and indexing
│   ├── milvus_utils.py     # Milvus DB helpers
│   └── ollama_utils.py     # Ollama API helpers
│
├── admin/
│   ├── auth.py             # Authentication logic
│   └── scheduler.py        # Scheduling logic
│
├── static/                 # CSS for Dash
└── templates/              # Custom HTML if needed
```

## Setup
1. Clone the repo
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python app.py`

## Components
- **Dash UI**: Admin panel (login, URL input, refresh, schedule) and chat interface
- **Web Scraper**: Recursively scrapes a website, generates embeddings, stores in Milvus
- **RAG Pipeline**: Translation, search, evaluation, and response agents
- **Session DB**: SQLite for user/session management

## Requirements
- Python 3.9+
- Ollama (for local LLM/embeddings)
- Milvus (vector DB)

## License
Apache 2.0
