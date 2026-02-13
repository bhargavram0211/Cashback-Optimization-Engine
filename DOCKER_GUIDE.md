# Docker Deployment Guide

## 🐳 Complete Dockerized Stack

The entire GetCardIQ application now runs in Docker containers for consistent deployment across all environments.

---

## 📦 Services

| Service | Container Name | Port | Description |
|---------|---------------|------|-------------|
| **Database** | `getcardiq_db` | 5432 | PostgreSQL 16 |
| **Backend** | `getcardiq_backend` | 8000 | FastAPI REST API |
| **Frontend** | `getcardiq_frontend_js` | 3000 | React Application (Vite dev server) |

---

## 🚀 Quick Start

### Start Everything

```bash
docker-compose up -d
```

This single command starts all 3 services!

### Access the Application

- **📊 Dashboard**: http://localhost:3000 (React UI)
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
docker-compose logs -f frontend-js
docker-compose logs -f backend
docker-compose logs -f db
```

### Restart a Service

```bash
docker-compose restart frontend-js
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
docker-compose up -d --build frontend-js

# Rebuild everything
docker-compose down
docker-compose up -d --build
```

---

## 🌐 Docker Networking

Services communicate via Docker's internal network:

```
Frontend (3000) - Vite dev server
    ↓
Backend (http://backend:8000)  ← Uses Docker service name
    ↓
Database (postgresql://db:5432)
```

**Key Point**: The frontend uses relative URLs (`/api/*`) that are proxied to the backend. In development, Vite's proxy configuration handles this automatically. In production, Nginx serves as a reverse proxy (see [DEPLOYMENT.md](./DEPLOYMENT.md) for production setup).

---

## 🔍 Troubleshooting

### Port Already in Use

**Error**: `bind: address already in use`

**Solution**:
```bash
# Find and kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9

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

**Check**: Frontend can reach backend via proxy
```bash
# Test from frontend container
docker-compose exec frontend-js wget -O- http://backend:8000/

# Or check Vite proxy configuration
docker-compose exec frontend-js cat vite.config.ts | grep proxy
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

1. **Edit** files in `frontend-js/src/`
2. **Changes auto-reload** (Vite HMR - Hot Module Replacement)
3. Browser automatically refreshes to show changes

### Backend Development

1. **Edit** files in `backend/app/`
2. **Changes auto-reload** (volume mounted, FastAPI `--reload` flag)
3. API updates immediately

### Database Changes

1. **Edit** `backend/app/models/models.py`
2. **Restart backend** to apply schema changes:
   ```bash
   docker-compose restart backend
   ```

---

## 📊 Health Checks

All services have health checks:

```bash
# Frontend health (Vite dev server)
curl http://localhost:3000

# Backend health
curl http://localhost:8000/

# Database health (from host)
docker-compose exec db pg_isready -U getcardiq_user
```

---

## 🎯 Production Considerations

### Environment Variables

For production, create a separate `.env.production`:

```bash
# Database
POSTGRES_USER=prod_user
POSTGRES_PASSWORD=<strong_password>
POSTGRES_DB=getcardiq_prod

# Plaid (production credentials)
PLAID_CLIENT_ID=<prod_client_id>
PLAID_SECRET=<prod_secret>
PLAID_ENV=production
```

Then use:
```bash
docker-compose --env-file .env.production up -d
```

### Production Deployment

For production deployment using pre-built images from a Docker registry, see **[DEPLOYMENT.md](./DEPLOYMENT.md)**.

The production setup uses:
- `docker-compose.prod.yml` for production configuration
- Pre-built images from Docker Hub or other registry
- Nginx reverse proxy for the frontend
- No volume mounts (static files)

### Scaling

To run multiple frontend instances (development):
```bash
docker-compose up -d --scale frontend-js=3
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
├── docker-compose.yml        # Development orchestration
├── docker-compose.prod.yml   # Production deployment (registry images)
├── backend/
│   └── Dockerfile            # Backend container definition
└── frontend-js/
    ├── Dockerfile            # Development container (Vite)
    ├── Dockerfile.prod       # Production container (Nginx)
    └── nginx.conf           # Nginx reverse proxy config
```

### docker-compose.yml Structure (Development)

```yaml
services:
  db:
    image: postgres:16
    ports: ["5432:5432"]
    healthcheck: ✓
  
  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db]
    volumes: [./backend:/app]  # Hot-reload
  
  frontend-js:
    build: ./frontend-js
    ports: ["3000:3000"]
    depends_on: [backend]
    volumes: [./frontend-js:/app]  # Hot-reload
    # Vite proxy configured in vite.config.ts
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
curl http://localhost:3000

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
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment guide
- [Frontend README](frontend-js/README.md) - Frontend-specific docs

