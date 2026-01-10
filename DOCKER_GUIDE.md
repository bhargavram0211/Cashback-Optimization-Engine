# Docker Deployment Guide

## 🐳 Complete Dockerized Stack

The entire Cashback Optimization Engine now runs in Docker containers for consistent deployment across all environments.

---

## 📦 Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **Database** | `cashback_db` | 5432 | PostgreSQL 16 |
| **Backend** | `cashback_backend` | 8000 | FastAPI REST API |
| **Frontend** | `cashback_frontend` | 8501 | Streamlit Dashboard |

---

## 🚀 Quick Start

### Start Everything

```bash
docker-compose up -d
```

This single command starts all 3 services!

### Access the Application

- **📊 Dashboard**: http://localhost:8501 (Streamlit UI)
- **🔌 API Backend**: http://localhost:8000 (REST API)
- **📚 API Docs**: http://localhost:8000/docs (Swagger UI)

---

## 🔧 Common Commands

### View Running Containers

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db
```

### Restart a Service

```bash
docker-compose restart frontend
docker-compose restart backend
```

### Stop Everything

```bash
docker-compose down
```

### Stop Everything + Delete Data

```bash
docker-compose down -v
```

### Rebuild After Code Changes

```bash
# Backend changes
docker-compose up -d --build backend

# Frontend changes
docker-compose up -d --build frontend

# Rebuild everything
docker-compose down
docker-compose up -d --build
```

---

## 🌐 Docker Networking

Services communicate via Docker's internal network:

```
Frontend (8501)
    ↓
Backend (http://backend:8000)  ← Uses Docker service name
    ↓
Database (postgresql://db:5432)
```

**Key Point**: The frontend uses `BACKEND_URL=http://backend:8000` (service name) instead of `localhost` because they're in the same Docker network.

---

## 🔍 Troubleshooting

### Port Already in Use

**Error**: `bind: address already in use`

**Solution**:
```bash
# Find and kill process on port 8501 (frontend)
lsof -ti:8501 | xargs kill -9

# Or port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Then restart
docker-compose up -d
```

### Frontend Can't Reach Backend

**Check**: Make sure backend is running and healthy
```bash
docker-compose ps
curl http://localhost:8000/
```

**Check**: Frontend environment variable
```bash
docker-compose exec frontend env | grep BACKEND_URL
# Should show: BACKEND_URL=http://backend:8000
```

### Database Connection Failed

**Check**: Database health
```bash
docker-compose ps db
# Should show "healthy"
```

**Restart** database:
```bash
docker-compose restart db
```

### Rebuild from Scratch

If things are really broken:
```bash
# Nuclear option: delete everything and start fresh
docker-compose down -v
docker system prune -f
docker-compose up --build -d
```

---

## 🔄 Development Workflow

### Frontend Development

1. **Edit** `frontend/app.py`
2. **Changes auto-reload** (volume mounted)
3. Refresh browser to see changes

### Backend Development

1. **Edit** `app/main.py` or other backend files
2. **Changes auto-reload** (volume mounted, `--reload` flag)
3. API updates immediately

### Database Changes

1. **Edit** `app/models/models.py`
2. **Restart backend** to apply schema changes:
   ```bash
   docker-compose restart backend
   ```

---

## 📊 Health Checks

All services have health checks:

```bash
# Frontend health
curl http://localhost:8501/_stcore/health

# Backend health
curl http://localhost:8000/

# Database health (from host)
docker-compose exec db pg_isready -U cashback_user
```

---

## 🎯 Production Considerations

### Environment Variables

For production, create a separate `.env.production`:

```bash
# Database
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=<strong_password>
POSTGRES_DB=cashback_prod

# Plaid (production credentials)
PLAID_CLIENT_ID=<prod_client_id>
PLAID_SECRET=<prod_secret>
PLAID_ENV=production
```

Then use:
```bash
docker-compose --env-file .env.production up -d
```

### Scaling

To run multiple frontend instances:
```bash
docker-compose up -d --scale frontend=3
```

### Logs

For production, consider using a log aggregation service:
```bash
docker-compose logs --follow | tee app.log
```

---

## 📄 Docker Files Overview

```
.
├── docker-compose.yml       # Orchestrates all 3 services
├── Dockerfile               # Backend container definition
└── frontend/
    └── Dockerfile           # Frontend container definition
```

### docker-compose.yml Structure

```yaml
services:
  db:
    image: postgres:16
    ports: ["5432:5432"]
    healthcheck: ✓
  
  backend:
    build: .
    ports: ["8000:8000"]
    depends_on: [db]
    volumes: [./app:/app/app]  # Hot-reload
  
  frontend:
    build: ./frontend
    ports: ["8501:8501"]
    depends_on: [backend]
    volumes: [./frontend:/app]  # Hot-reload
    environment:
      BACKEND_URL: http://backend:8000
```

---

## ✅ Verify Complete Stack

Run this to test everything:

```bash
# 1. Check all containers are healthy
docker-compose ps

# 2. Test backend
curl http://localhost:8000/

# 3. Test frontend
curl http://localhost:8501/_stcore/health

# 4. Test end-to-end (from frontend to backend)
curl -s "http://localhost:8000/reports/savings/4b0939d1-7595-414e-bbd9-597f41c39e99" | jq '.summary'
```

If all return successful responses, your stack is fully operational! 🎉

---

## 🎓 Benefits of Docker Deployment

✅ **Consistency**: Same environment everywhere (dev, staging, prod)  
✅ **Isolation**: No conflicts with other projects  
✅ **Simplicity**: One command to start everything  
✅ **Portability**: Works on any machine with Docker  
✅ **Reproducibility**: Exact versions of all dependencies  
✅ **Scalability**: Easy to add more services or scale existing ones  

---

For more details, see:
- [Main README](README.md) - Project overview
- [Frontend README](frontend/README.md) - Frontend-specific docs
- [LEARNINGS.md](LEARNINGS.md) - Troubleshooting guide

