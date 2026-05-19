# PyDocAi - Project Overview

## Project Description

PyDocAi is an AI-powered documentation generator that parses Python code and automatically generates documentation using AI. It consists of a Django REST API backend and a React frontend, with PostgreSQL for data storage and Celery for async task processing.

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API    │────▶│  PostgreSQL     │
│   (React +      │     │   (Django DRF)   │     │   Database      │
│   Vite + TS)    │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐     ┌─────────────────┐
                         │  Celery Worker  │────▶│     Redis       │
                         │  (Async Tasks)  │     │   (Broker)      │
                         └─────────────────┘     └─────────────────┘
```

---

## Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Django 5.x | Web framework |
| Django REST Framework | REST API |
| PostgreSQL | Database |
| Redis + Celery | Async task queue |
| SimpleJWT | JWT Authentication |
| Python AST | Code parsing |

### Frontend
| Technology | Purpose |
|------------|---------|
| React 19 | UI framework |
| Vite | Build tool |
| TypeScript | Type safety |
| Tailwind CSS | Styling |
| React Router | Navigation |
| Axios | HTTP client |

### Infrastructure
| Service | Port | Description |
|---------|------|-------------|
| backend | 8000 | Django API |
| frontend | 5173/80 | React app |
| db | 5432 | PostgreSQL |
| redis | 6379 | Celery broker |

---

## App Modules

### 1. users
**Purpose:** User authentication and management
- Custom user model extending `AbstractBaseUser`
- JWT-based authentication
- Registration, login, password change endpoints

### 2. projects
**Purpose:** Project management
- `Project` model - represents a documentation project
- `ProjectFile` model - represents files within a project
- CRUD operations for projects

### 3. parser
**Purpose:** Python code parsing
- `ast_parser.py` - parses Python files using AST
- `validators.py` - validates Python syntax
- `tasks.py` - Celery tasks for async parsing
- Handles file/folder analysis

### 4. ai
**Purpose:** AI-powered documentation generation
- `generator.py` - generates documentation using AI
- `prompts.py` - builds prompts for AI model
- Integrates with Groq API for LLM responses

### 5. github_integration
**Purpose:** GitHub API integration
- Fetch repository data
- OAuth/token-based authentication with GitHub

### 6. exports
**Purpose:** Export functionality
- Export projects as Markdown
- `generators.py` - creates markdown output

---

## Data Models

### User
```
- id (UUID)
- email (unique)
- username
- password (hashed)
- is_active
- is_staff
- is_superuser
- date_joined
```

### Project
```
- id (UUID)
- name
- description
- status (pending/processing/completed/failed)
- user (FK to User)
- created_at
- updated_at
```

### ProjectFile
```
- id (UUID)
- project (FK to Project)
- file_name
- file_path
- file_content
- documentation
- created_at
```

---

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register/` | POST | Register new user |
| `/api/auth/login/` | POST | Login (get JWT) |
| `/api/auth/logout/` | POST | Logout (blacklist token) |
| `/api/auth/profile/` | GET/PUT | Get/update user profile |
| `/api/auth/change-password/` | POST | Change password |

### Projects
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/projects/` | GET | List user's projects |
| `/api/projects/` | POST | Create new project |
| `/api/projects/{id}/` | GET | Get project details |
| `/api/projects/{id}/` | DELETE | Delete project |

### Parser
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/parser/analyze-file/` | POST | Analyze single file |
| `/api/parser/analyze-folder/` | POST | Analyze folder (ZIP) |

### Exports
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/exports/markdown/{id}/` | GET | Export project as Markdown |

---

## Async Tasks (Celery)

### parse_folder_task
- Extracts Python files from ZIP
- Parses each file using AST
- Stores parsed data in database
- Retry mechanism with exponential backoff

### parse_and_generate_docs_task
- Parses single Python file
- Generates AI documentation
- Updates ProjectFile with documentation

---

## Configuration

### Environment Variables
- `DJANGO_SECRET_KEY` - Django secret key
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `GROQ_API_KEY` - Groq AI API key (for documentation generation)

### Settings
- JWT token lifetime: 60 minutes (access), 7 days (refresh)
- Celery task timeout: 30 minutes

---

## Quick Start

### With Docker
```bash
docker-compose up --build
```

### Without Docker
```bash
# Backend
cd backend
uv venv
uv run python manage.py migrate
uv run python manage.py runserver

# Frontend
cd frondend
npm install
npm run dev
```

---

## File Structure

```
PyDocAi/
├── backend/
│   ├── apps/
│   │   ├── users/        # User authentication
│   │   ├── projects/     # Project management
│   │   ├── parser/       # Code parsing
│   │   ├── ai/          # AI documentation
│   │   ├── github_integration/  # GitHub API
│   │   └── exports/     # Export functionality
│   ├── config/          # Django settings
│   └── requirements/    # Dependencies
├── frondend/
│   ├── src/             # React components
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

*Generated for PyDocAi Project Documentation*