# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack & Architecture

**Devopin Community Backend** - A hybrid monitoring and management application combining FastAPI REST API with NiceGUI web interface.

- **FastAPI** + **NiceGUI** - Web framework and UI components running on single server
- **SQLAlchemy** + **Alembic** - ORM and database migrations 
- **SQLite** database (`devopin.db`)
- **Unix socket communication** with external `devopin-agent`
- **Real-time monitoring** via WebSockets and SocketIO

## Code Architecture

```
app/
├── api/route.py          # REST API endpoints (/api/*)
├── core/                 # Database config and connection
├── models/              # SQLAlchemy database models
├── schemas/             # Pydantic validation schemas  
├── services/            # Business logic and CRUD operations
├── ui/                  # NiceGUI web interface components
└── utils/agent_controller.py  # Unix socket communication with devopin-agent
```

**Layered Architecture:**
- **API Layer** (`app/api/`) - REST endpoints for external monitoring data ingestion
- **UI Layer** (`app/ui/`) - NiceGUI-based web interface (auth, dashboard, project management)
- **Service Layer** (`app/services/`) - Business logic and database operations
- **Model Layer** (`app/models/`) - Database schema definitions

## Development Commands

**Run Application:**
```bash
python -m app.main
# or with uvicorn
uvicorn app.main:app --reload
```

**Database Management:**
```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

**Configuration:**
- Uses `.env` file (see `.env.example`)
- Default database: `sqlite:///./devopin.db`

## Key Features

**Agent Communication:**
- Communicates with external `devopin-agent` via Unix socket
- Production socket: `/run/devopin-agent.sock`
- Development socket: `/tmp/devopin-agent.sock`
- Auto-fallback between production and development paths

**Monitoring System:**
- Ingests monitoring data via `/api/monitoring-data` endpoint
- Real-time system metrics (CPU, memory, disk usage)
- Service worker status tracking
- Project log aggregation
- Interactive dashboard with live charts

**Web Interface:**
- User authentication system
- Real-time dashboard with performance visualization
- Project and service worker management
- Responsive design with glassmorphism styling

## Application Entry Point

`app/main.py:17` - Main application startup with NiceGUI server configuration:
- Combines FastAPI router with NiceGUI pages
- Runs with hot reload enabled
- Routes root `/` to `/login`

## Important File Locations

- **Socket Communication:** `app/utils/agent_controller.py:15` - AgentController class
- **Database Config:** `alembic.ini:87` - SQLAlchemy URL configuration  
- **API Routes:** `app/api/route.py` - All REST API endpoints
- **Main Models:** `app/models/` - User, Project, ServiceWorker, MonitoringData, ProjectLog