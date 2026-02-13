# Deployment Guide

This guide explains how to build, push, and deploy GetCardIQ using Docker images from a registry.

## Prerequisites

- Docker installed and running
- Docker Compose installed
- Docker Hub account (or access to another Docker registry)
- `.env` file configured with your environment variables

## Architecture: Reverse Proxy Pattern

The application uses a **reverse proxy pattern** where:
- Frontend uses relative URLs (`/api/*`) instead of absolute backend URLs
- Nginx (in frontend container) proxies `/api/*` requests to the backend
- This enables true pull-and-run deployment - no build-time configuration needed

**Benefits:**
- Pre-built images work everywhere (no IP/domain configuration)
- Simpler deployment (one domain/IP for everything)
- Better security (backend not directly exposed)
- No CORS issues (same-origin requests)

## Quick Start (Using Pre-built Images)

If images are already available in a Docker registry:

1. **Create `.env` file:**
   ```bash
   cp env.example .env
   # Edit .env with your values (Plaid credentials, database passwords)
   # For production, set IMAGE_TAG=stable_v1 to use the current stable release
   ```

2. **Update `docker-compose.prod.yml` (or set in `.env`):**
   - Set `IMAGE_REGISTRY_USERNAME` to your Docker Hub username
   - Set `IMAGE_TAG=stable_v1` to use the current stable tag (default is `latest`)

3. **Pull and start services:**
   ```bash
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000 (or your domain/IP)
   - Backend API (via proxy): http://localhost:3000/api/*
   - API Docs (direct): http://localhost:8000/docs

## Building and Pushing Images

### 1. Build Backend Image

```bash
cd backend
docker build -t your-dockerhub-username/getcardiq-backend:latest .
docker push your-dockerhub-username/getcardiq-backend:latest
```

### 2. Build Frontend Image

**No build arguments needed!** The frontend uses relative URLs (`/api`) that Nginx proxies to the backend.

```bash
cd frontend-js
docker build \
  -f Dockerfile.prod \
  -t your-dockerhub-username/getcardiq-frontend:latest .
docker push your-dockerhub-username/getcardiq-frontend:latest
```

**Note:** The frontend image works everywhere because it uses relative URLs. Nginx handles proxying to the backend automatically.

### 3. Tagging for Versioning

**Current stable tag:** `stable_v1` — use this tag for production deployments.

For production, tag and push with the stable tag (or semantic versions):

```bash
# Tag and push with current stable tag
docker tag your-dockerhub-username/getcardiq-backend:latest \
  your-dockerhub-username/getcardiq-backend:stable_v1
docker push your-dockerhub-username/getcardiq-backend:stable_v1

docker tag your-dockerhub-username/getcardiq-frontend:latest \
  your-dockerhub-username/getcardiq-frontend:stable_v1
docker push your-dockerhub-username/getcardiq-frontend:stable_v1
```

Optional: also tag with semantic version (e.g. v1.0.0):

```bash
# Backend
docker tag your-dockerhub-username/getcardiq-backend:latest \
  your-dockerhub-username/getcardiq-backend:v1.0.0
docker push your-dockerhub-username/getcardiq-backend:v1.0.0

# Frontend
docker tag your-dockerhub-username/getcardiq-frontend:latest \
  your-dockerhub-username/getcardiq-frontend:v1.0.0
docker push your-dockerhub-username/getcardiq-frontend:v1.0.0
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `getcardiq_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `your_secure_password` |
| `POSTGRES_DB` | PostgreSQL database name | `getcardiq_db` |
| `PLAID_CLIENT_ID` | Plaid API client ID | `your_plaid_client_id` |
| `PLAID_SECRET` | Plaid API secret | `your_plaid_secret` |
| `PLAID_ENV` | Plaid environment | `sandbox` or `production` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IMAGE_REGISTRY_USERNAME` | Docker Hub or registry username for image names | (set in .env) |
| `IMAGE_TAG` | Image tag to pull/deploy. **Current stable tag:** `stable_v1` | `latest` |
| `BACKEND_URL` | **Deprecated** - No longer needed due to reverse proxy | N/A |
| `CORS_ORIGINS` | Comma-separated allowed origins (less critical with reverse proxy) | `http://localhost:3000,...` |

### Setting CORS_ORIGINS

The backend CORS configuration accepts a comma-separated list of origins:

```bash
# Single origin
CORS_ORIGINS=http://localhost:3000

# Multiple origins
CORS_ORIGINS=http://localhost:3000,http://your-domain.com,https://your-domain.com
```

## Development vs Production

### Development Setup

Uses `docker-compose.yml`:
- Builds images locally
- Volume mounts for hot-reload
- Development server (Vite dev server)
- Platform-specific (arm64)

```bash
docker-compose up --build
```

### Production Setup

Uses `docker-compose.prod.yml`:
- Pulls pre-built images from registry
- No volume mounts (static files)
- Production server (Nginx)
- Multi-platform support

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Frontend Can't Connect to Backend

**Symptom:** Frontend shows connection errors or API requests fail

**Solutions:**
1. Verify backend is running: `docker-compose ps backend`
2. Check backend logs: `docker-compose logs backend`
3. Verify frontend container can reach backend: `docker-compose exec frontend-js ping backend`
4. Check nginx logs in frontend container: `docker-compose logs frontend-js`
5. Ensure both services are on the same Docker network (default network is fine)
6. Test backend directly: `curl http://localhost:8000/` (should return `{"status": "Backend is Online"}`)

### Database Connection Fails

**Symptom:** Backend logs show database connection errors

**Solutions:**
1. Verify database is healthy: `docker-compose ps db`
2. Check `DATABASE_URL` format in `.env`
3. Ensure database service starts before backend (healthcheck)
4. Check database logs: `docker-compose logs db`

### Images Not Found

**Symptom:** `docker-compose.prod.yml` fails with "image not found"

**Solutions:**
1. Verify image names in `docker-compose.prod.yml` match registry
2. Ensure images are pushed: `docker images | grep getcardiq`
3. Check Docker Hub login: `docker login`
4. Pull images manually: `docker pull your-username/getcardiq-backend:latest`

### API Requests Return 502 Bad Gateway

**Symptom:** Frontend shows 502 errors when making API calls

**Cause:** Nginx can't reach the backend service

**Solutions:**
1. Verify backend service name matches nginx config (`backend:8000`)
2. Check backend is healthy: `docker-compose ps backend`
3. Test backend connectivity from frontend container:
   ```bash
   docker-compose exec frontend-js wget -O- http://backend:8000/
   ```
4. Verify both services are on same network: `docker network inspect <network-name>`
5. Check nginx configuration: `docker-compose exec frontend-js cat /etc/nginx/conf.d/default.conf`

## Multi-Platform Builds

To support both ARM64 and AMD64:

```bash
# Install buildx
docker buildx create --use

# Build frontend for multiple platforms (no build args needed)
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f frontend-js/Dockerfile.prod \
  -t your-username/getcardiq-frontend:latest \
  --push \
  frontend-js/

# Build backend for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-username/getcardiq-backend:latest \
  --push \
  backend/
```

## Security Considerations

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use strong passwords** - Especially for `POSTGRES_PASSWORD`
3. **Limit CORS origins** - Only include trusted domains
4. **Use secrets management** - For production, consider Docker secrets or external secret managers
5. **Keep images updated** - Regularly rebuild and push updated images

## Stopping Services

```bash
# Stop containers (keeps data)
docker-compose -f docker-compose.prod.yml down

# Stop and remove volumes (clears database)
docker-compose -f docker-compose.prod.yml down -v
```

## Next Steps

- Set up CI/CD pipeline to automatically build and push images
- Configure reverse proxy (nginx/traefik) for production
- Set up monitoring and logging
- Configure SSL/TLS certificates
- Set up database backups
