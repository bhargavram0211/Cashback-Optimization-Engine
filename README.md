# Cashback Optimization Engine

A financial analysis tool designed to ingest credit card transactions via Plaid and identify "Opportunity Costs" where a different card in your portfolio would have yielded higher rewards.

## 🚀 Quick Start (Sub-Phase 1.1: Infrastructure Shell)

This setup provides a minimal, stable environment where a FastAPI container can communicate with a PostgreSQL 16 container on your MacBook M2 (arm64).

### Prerequisites

- Docker Desktop for Mac (with Apple Silicon support)
- MacBook M2 (arm64 architecture)

### Setup Instructions

1. **Create the environment file**
   ```bash
   cp env.example .env
   ```
   
   The `.env` file contains default credentials for local development. You can modify them if needed.

2. **Build and start the containers**
   ```bash
   docker-compose up --build
   ```
   
   This will:
   - Start a PostgreSQL 16 database on port 5432
   - Build and start the FastAPI backend on port 8000
   - Wait for the database to be healthy before starting the backend

3. **Verify the setup**
   
   Open your browser and test these endpoints:
   
   - **Backend Health Check**: http://localhost:8000/
     - Expected response: `{"status": "Backend is Online"}`
   
   - **Database Connection Test**: http://localhost:8000/db-test
     - Expected response: `{"status": "Database Connected"}`

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check - verifies backend is running |
| `/db-test` | GET | Database connectivity test |
| `/docs` | GET | Auto-generated API documentation (Swagger UI) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |

### Docker Services

- **db**: PostgreSQL 16 database
  - Port: 5432
  - Platform: linux/arm64
  - Healthcheck enabled
  
- **backend**: FastAPI application
  - Port: 8000
  - Platform: linux/arm64
  - Hot-reload enabled (code changes reflect automatically)

### Stopping the Services

```bash
# Stop containers (keeps data)
docker-compose down

# Stop containers and remove volumes (clears database)
docker-compose down -v
```

### Troubleshooting

**Database connection fails:**
- Ensure Docker Desktop is running
- Check if port 5432 is available: `lsof -i :5432`
- Verify the database is healthy: `docker-compose ps`

**Backend not accessible:**
- Ensure port 8000 is available: `lsof -i :8000`
- Check backend logs: `docker-compose logs backend`

**Build fails:**
- Clear Docker cache: `docker-compose build --no-cache`
- Ensure you're using the latest Docker Desktop for Apple Silicon

## 📁 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API endpoints (future)
│   ├── core/                # Core configurations (future)
│   ├── logic/               # Business logic (future)
│   └── models/              # Database models (future)
├── docker-compose.yml       # Multi-container orchestration
├── Dockerfile               # Backend container definition
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🛠️ Tech Stack

- **Backend**: Python 3.12+ with FastAPI
- **Database**: PostgreSQL 16
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Containerization**: Docker & Docker Compose
- **Platform**: Optimized for MacBook M2 (arm64)

## 📝 Next Steps

This is Sub-Phase 1.1: Infrastructure Shell. The following phases will add:
- Database models (User, PlaidItem, Card, Transaction)
- Plaid integration
- Category normalization
- Optimization engine
- Streamlit dashboard

## 📄 License

This is a private development project.
