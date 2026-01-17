# Cashback Optimizer - React Frontend

Modern React + TypeScript frontend for the Cashback Optimization Engine.

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

Create a `.env` file in the `frontend-js` directory:

```env
VITE_BACKEND_URL=http://localhost:8000
```

For Docker, the backend URL is automatically set to `http://backend:8000`.

## Docker

### Development Mode

The Dockerfile runs the Vite dev server with hot reload:

```bash
docker-compose up frontend-js
```

The app will be available at `http://localhost:3000`

### Building for Production

To build for production:

```bash
npm run build
```

The built files will be in the `dist/` directory.

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
└── Dockerfile
```

## Features Implemented (Part 1)

- ✅ Authentication (signup, login, logout)
- ✅ Session management with persistence
- ✅ Protected routes
- ✅ Landing page with signup/login forms
- ✅ Dashboard placeholder (protected route)

## Next Steps (Part 2)

- Dashboard with savings insights
- Card Discovery page
- Identify Cards page
- Onboarding flow
