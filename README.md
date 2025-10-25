# Ekam - NLP Query Engine for Employee Data

A sophisticated natural language processing system that enables users to query employee databases using natural language. The system features dynamic schema discovery, document processing, and hybrid query processing capabilities.

## Features

- **Natural Language Queries**: Query your database using plain English
- **Dynamic Schema Discovery**: Automatically discover and map database schemas
- **Document Processing**: Upload and process PDF, DOCX, TXT, and CSV files
- **Hybrid Query Processing**: Combines SQL generation with document search
- **Real-time Health Monitoring**: Comprehensive system health tracking
- **Modern Web Interface**: React-based frontend with intuitive UI
- **Scalable Architecture**: Microservices-based design with Docker support

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Databases     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   PostgreSQL    │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Cache   │    │   ChromaDB      │
                       │   Port: 6379    │    │   Port: 8001    │
                       └─────────────────┘    └─────────────────┘
```

## Prerequisites

- **Docker Desktop** (for containerized services)
- **Python 3.9+** (for local development)
- **Node.js 16+** (for frontend development)
- **Git** (for version control)

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Ekam
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env file with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Windows Batch Script

1. **Run the start script**
   ```cmd
   start.bat
   ```

2. **The script will automatically:**
   - Check Docker status
   - Start database services
   - Launch backend and frontend
   - Open the application in your browser

### Option 3: Manual Setup

#### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp ../env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the backend**
   ```bash
   python main.py
   ```

#### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the frontend**
   ```bash
   npm start
   ```

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://admin:password@localhost:5432/employee_nlp_db
POSTGRES_DB=employee_nlp_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=password

# Redis Configuration
REDIS_URL=redis://localhost:6379

# ChromaDB Configuration
CHROMA_URL=http://localhost:8001

# API Configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# Security Configuration
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance Configuration
MAX_CONCURRENT_QUERIES=10
CACHE_TTL=300
BATCH_SIZE=32

# File Upload Configuration
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=pdf,docx,txt,csv

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
```

### Required API Keys

- **Mistral API Key**: Required for natural language processing
  - Sign up at [Mistral AI](https://mistral.ai/)
  - Get your API key from the dashboard
  - Add it to your `.env` file

## Services

### Core Services

| Service     | Port | Description         |
|-------------|------|---------------------|
| Frontend    | 3000 | React web interface |
| Backend API | 8000 | FastAPI backend     |
| PostgreSQL  | 5432 | Primary database    |
| Redis       | 6379 | Caching layer       |
| ChromaDB    | 8001 | Vector database     |

### Health Monitoring

- **Health Check**: `GET /health`
- **Database Status**: `GET /database/status`
- **Comprehensive Health**: `GET /health/comprehensive`
- **Health Alerts**: `GET /health/alerts`
- **Health History**: `GET /health/history`

## Testing

### Run Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test

# Integration tests
cd backend
python -m pytest tests/test_integration.py
```

### Performance Testing

```bash
cd backend
python -m pytest tests/test_performance.py
```

## Project Structure

```
Ekam/
├── backend/                 # FastAPI backend
│   ├── api/                # API layer
│   │   ├── endpoints/      # API endpoints
│   │   ├── models/         # Data models
│   │   ├── routes/         # Route handlers
│   │   └── services/       # Business logic
│   ├── alembic/           # Database migrations
│   ├── tests/             # Test suite
│   └── main.py          # Application entry point
├── frontend/              # React frontend
│   ├── src/               # Source code
│   │   ├── components/    # React components
│   │   └── services/       # API services
│   └── public/            # Static assets
├── docs/                  # Documentation
├── monitoring/            # Monitoring configuration
├── scripts/               # Utility scripts
└── docker-compose.yml     # Docker services
```

## API Endpoints

### Schema Management
- `GET /schema/discover` - Discover database schema
- `GET /schema/tables` - List all tables
- `GET /schema/columns/{table}` - Get table columns

### Document Processing
- `POST /documents/upload` - Upload documents
- `GET /documents/list` - List uploaded documents
- `DELETE /documents/{id}` - Delete document

### Query Processing
- `POST /query/natural` - Process natural language query
- `POST /query/sql` - Execute SQL query
- `GET /query/history` - Query history

### Data Ingestion
- `POST /ingestion/connect` - Connect to database
- `POST /ingestion/sync` - Sync database schema
- `GET /ingestion/status` - Ingestion status

## Deployment

### Production Deployment

1. **Use production Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Configure production environment**
   ```bash
   cp env.prod .env
   # Edit with production values
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

### Monitoring

- **Grafana Dashboard**: http://localhost:3001
- **Prometheus Metrics**: http://localhost:9090
- **Application Logs**: Check `logs/` directory

## Development

### Code Quality

```bash
# Backend linting
cd backend
black .
flake8 .

# Frontend linting
cd frontend
npm run lint
```

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Troubleshooting

### Common Issues

1. **Docker not running**
   - Start Docker Desktop
   - Check Docker status: `docker info`

2. **Port conflicts**
   - Check if ports 3000, 8000, 5432, 6379, 8001 are available
   - Stop conflicting services

3. **Database connection issues**
   - Verify PostgreSQL is running
   - Check connection string in `.env`
   - Run migrations: `alembic upgrade head`

4. **API key issues**
   - Verify Mistral API key is valid
   - Check API key in `.env` file

### Logs

- **Application logs**: `backend/app.log`
- **Docker logs**: `docker-compose logs [service]`
- **System logs**: Check `logs/` directory

## Documentation

- [Infrastructure Setup](docs/SECTION_1_INFRASTRUCTURE.md)
- [Database Configuration](docs/SECTION_2_DATABASE.md)
- [Schema Discovery](docs/SECTION_3_SCHEMA_DISCOVERY.md)
- [Document Processing](docs/SECTION_4_DOCUMENT_PROCESSING.md)
- [Query Engine](docs/SECTION_5_QUERY_ENGINE.md)
- [API Layer](docs/SECTION_6_API_LAYER.md)
- [Frontend](docs/SECTION_7_FRONTEND.md)
- [Integration](docs/SECTION_8_INTEGRATION.md)
- [Deployment](docs/SECTION_9_DEPLOYMENT.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request


## Support

For support and questions:

- Open an issue on GitHub

## Updates

To update the application:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose down
docker-compose up -d --build
```

---

**Happy Querying!**