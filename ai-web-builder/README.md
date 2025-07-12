# AI Web Builder

Silicon Valley-quality web builder with AI-powered component generation for SMBs.

## Architecture

- **Frontend**: Next.js 14 (React 18, TypeScript, Tailwind CSS)
- **Backend**: FastAPI (Python 3.11+)
- **AI Integration**: Multi-modal AI for component generation
- **Database**: PostgreSQL + Redis for caching
- **Deployment**: Docker containers

## Project Structure

```
ai-web-builder/
├── frontend/          # Next.js application
├── backend/           # FastAPI server
├── shared/            # Shared types and utilities
├── docs/              # Documentation
└── docker-compose.yml # Development environment
```

## Getting Started

1. Clone the repository
2. Run `docker-compose up` for development
3. Frontend: http://localhost:3000
4. Backend API: http://localhost:8000