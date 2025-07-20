# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack & Architecture

**Devopin Community Backend** - A hybrid monitoring and management application combining FastAPI REST API with NiceGUI web interface.

- **FastAPI** + **NiceGUI** - Web framework and UI components running on single server
- **SQLAlchemy** + **Alembic** - ORM and database migrations 
- **SQLite** database (`devopin.db`)
- **Unix socket communication** with external `devopin-agent`
- **Real-time monitoring** via WebSockets and SocketIO
- **PyInstaller** for executable builds
- **Docker** containerization with health checks

## Code Architecture

```
app/
├── api/route.py          # REST API endpoints (/api/*)
├── core/                 # Database config, logging, authentication
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

**Local Development:**
```bash
# Run with hot reload
python -m app.main

# Or with uvicorn
uvicorn app.main:app --reload

# Set RELOAD=true in .env for development mode
```

**Docker Development:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Database Management:**
```bash
# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

**Build & Release:**
```bash
# Build release assets with version
./build-release.sh [version]

# Build executable manually
pyinstaller build.spec --name "devopin-app-linux-amd64" --onefile --clean --noconfirm
```

## Environment Configuration

**Critical Environment Variables** (from `.env.example`):
- **DATABASE_URL**: `sqlite:////app/data/devopin.db`
- **SECRET_KEY**: Must change in production for security
- **STORAGE_SECRET**: Must change in production for security
- **AGENT_SOCKET_PATH**: `/run/devopin-agent.sock` (production)
- **FALLBACK_SOCKET_PATH**: `/tmp/devopin-agent.sock` (development)
- **HOST**: `0.0.0.0`, **PORT**: `8080`
- **CPU_THRESHOLD**: `80`, **MEMORY_THRESHOLD**: `85`, **DISK_THRESHOLD**: `90`

## Logging System

**Log Files Structure:**
- `logs/app_YYYYMMDD.log` - Main application logs (INFO level)
- `logs/debug_YYYYMMDD.log` - Debug logs (DEBUG level)  
- `logs/error_YYYYMMDD.log` - Error logs (ERROR level)
- **Rotating handlers**: 10MB max size, 5 backup files

## Key Features

**Agent Communication:**
- Communicates with external `devopin-agent` via Unix socket
- Production socket: `/run/devopin-agent.sock`
- Development socket: `/tmp/devopin-agent.sock`
- Auto-fallback between production and development paths
- Socket timeout: 5 seconds (configurable via `AGENT_TIMEOUT`)

**Monitoring & Threshold System:**
- Ingests monitoring data via `/api/monitoring-data` endpoint
- Real-time system metrics (CPU, memory, disk usage)
- **Automatic alarm creation** when thresholds exceeded
- Service worker status tracking with threshold monitoring
- Project log aggregation with threshold-based alerting
- Interactive dashboard with live charts via NiceGUI-Highcharts

**Web Interface:**
- User authentication with Argon2 password hashing
- Real-time dashboard with performance visualization
- Project and service worker management
- Alarm management system (acknowledge, resolve)
- Threshold configuration interface
- Responsive design with glassmorphism styling

**Docker Production Features:**
- Health check endpoint: `/api/health`
- Volume persistence for database: `./devopin-data:/app/data`
- Socket mounting for agent communication
- Container runs as non-root user in production

## API Endpoints

**Primary Data Ingestion:**
- `POST /api/monitoring-data` - Real-time monitoring data ingestion
- `GET /api/health` - Container health check endpoint

**Management APIs:**
- Authentication, user management
- Project and service worker CRUD operations
- Alarm management (create, acknowledge, resolve)
- Threshold configuration management

## Application Entry Point

`app/main.py:17` - Main application startup with NiceGUI server configuration:
- Combines FastAPI router with NiceGUI pages
- Runs with hot reload enabled in development
- Routes root `/` to `/login`
- Integrates SocketIO for real-time updates

## Important File Locations

- **Socket Communication:** `app/utils/agent_controller.py:15` - AgentController class
- **Database Config:** `alembic.ini:87` - SQLAlchemy URL configuration  
- **API Routes:** `app/api/route.py` - All REST API endpoints
- **Logging Config:** `app/core/logging_config.py` - Comprehensive logging setup
- **Authentication:** `app/core/auth.py` - JWT token management, password hashing
- **Main Models:** `app/models/` - User, Project, ServiceWorker, MonitoringData, ProjectLog, Alarm, Threshold
- **Build Configuration:** `build.spec` - PyInstaller configuration with 150+ hidden imports
- **Docker Config:** `docker-compose.yml` - Production deployment configuration