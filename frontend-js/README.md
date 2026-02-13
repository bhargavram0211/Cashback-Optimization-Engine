# GetCardIQ - React Frontend

Modern React + TypeScript frontend for GetCardIQ.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router v6** - Routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Tailwind CSS** - Styling

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

**No environment variables needed for local development!**

The frontend uses relative URLs (`/api/*`) that are automatically proxied to the backend:
- **Local development**: Vite's proxy configuration (see `vite.config.ts`) handles routing
- **Docker development**: Vite proxy configured to use `http://backend:8000`
- **Production**: Nginx reverse proxy handles routing (see `nginx.conf`)

This reverse proxy pattern means no build-time configuration is required - the same image works everywhere.

## Docker

### Development Mode

The `Dockerfile` runs the Vite dev server with hot reload:

```bash
docker-compose up frontend-js
```

The app will be available at `http://localhost:3000`

**Note**: API calls use relative URLs (`/api/*`) which Vite automatically proxies to `http://backend:8000` based on the configuration in `vite.config.ts`.

### Production Build

For production deployment, use `Dockerfile.prod`:

```bash
docker build -f Dockerfile.prod -t your-username/getcardiq-frontend:latest .
```

This creates a multi-stage build:
1. **Builder stage**: Compiles React app with Vite
2. **Production stage**: Serves static files with Nginx

The production image uses Nginx as a reverse proxy:
- Serves static files from `/usr/share/nginx/html`
- Proxies `/api/*` requests to the backend service
- No build-time configuration needed (works with any backend URL)

See [DEPLOYMENT.md](../DEPLOYMENT.md) for complete production deployment instructions.

## Project Structure

```
frontend-js/
├── src/
│   ├── api/          # API client and endpoints
│   ├── components/   # Reusable UI components
│   ├── pages/        # Page components
│   ├── store/        # Zustand stores
│   ├── types/        # TypeScript type definitions
│   ├── App.tsx       # Main app component
│   ├── main.tsx      # Entry point
│   └── index.css     # Global styles
├── package.json
├── vite.config.ts
├── tsconfig.json
├── Dockerfile          # Development (Vite dev server)
├── Dockerfile.prod     # Production (Nginx)
└── nginx.conf          # Nginx reverse proxy config
```

## Features Implemented

- ✅ Authentication (signup, login, logout)
- ✅ Session management with persistence
- ✅ Protected routes
- ✅ Dashboard with savings insights and metrics
- ✅ Card Discovery page with filtering
- ✅ Card Identification workflow
- ✅ Bank Management interface
- ✅ Mobile-responsive design
- ✅ Production-ready deployment with Nginx
