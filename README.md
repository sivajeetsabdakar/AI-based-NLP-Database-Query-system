# NLP Query Engine for Employee Data

A natural language query system for employee databases that dynamically adapts to the actual schema and can handle both structured employee data and unstructured documents. The system works without hard-coding table names, column names, or relationships.

## Features

- **Dynamic Schema Discovery**: Automatically discovers database structure and relationships
- **Natural Language Processing**: Converts user queries to SQL and document searches
- **Multi-modal Data**: Handles both structured database data and unstructured documents
- **Production-Ready**: Supports concurrent users, caching, and performance optimization
- **Adaptive**: Works with varying database schemas without code changes

## Technology Stack

- **Backend**: FastAPI (Python 3.9+)
- **Frontend**: React with Bootstrap
- **Database**: PostgreSQL
- **Vector Database**: ChromaDB
- **Cache**: Redis
- **LLM**: Mistral API (free tier)
- **Deployment**: Docker containers

## Project Structure

```
project/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── ingestion.py
│   │   │   ├── query.py
│   │   │   └── schema.py
│   │   ├── services/
│   │   │   ├── schema_discovery.py
│   │   │   ├── document_processor.py
│   │   │   └── query_engine.py
│   │   └── models/
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DatabaseConnector.js
│   │   │   ├── DocumentUploader.js
│   │   │   ├── QueryPanel.js
│   │   │   └── ResultsView.js
│   │   └── App.js
│   └── public/
├── docker-compose.yml
├── requirements.txt
├── package.json
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd nlp-query-engine
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## API Endpoints

### Data Ingestion
- `POST /api/ingest/database` - Connect to database and discover schema
- `POST /api/ingest/documents` - Upload documents for processing
- `GET /api/ingest/status` - Check ingestion progress

### Query Processing
- `POST /api/query` - Process natural language query
- `GET /api/query/history` - Get previous queries

### Schema Management
- `GET /api/schema` - Get discovered schema
- `POST /api/schema/refresh` - Refresh schema discovery

## Development Status

This project is currently in **Section 1: Project Infrastructure Setup**.

### Completed
- ✅ Project directory structure
- ✅ Basic FastAPI backend setup
- ✅ React frontend setup
- ✅ Docker configuration
- ✅ Environment configuration

### In Progress
- 🔄 Section 1 implementation

### Upcoming
- ⏳ Section 2: Database Layer Implementation
- ⏳ Section 3: Schema Discovery Engine
- ⏳ Section 4: Document Processing Pipeline
- ⏳ Section 5: Query Processing Engine
- ⏳ Section 6: API Layer Implementation
- ⏳ Section 7: Frontend Implementation
- ⏳ Section 8: Integration and Testing
- ⏳ Section 9: Deployment and Production Setup

## Contributing

This project follows a structured implementation plan with 9 sections. Each section builds upon the previous ones to create a complete NLP query engine.

## License

This project is part of an AI Engineering assignment for building a natural language query system for employee data.
