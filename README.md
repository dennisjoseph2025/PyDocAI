# PyDocAi

AI-powered documentation generator.

## Quick Start with Docker

### Development
```bash
docker-compose -f docker-compose.dev.yml up --build
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

### Production
```bash
docker-compose up --build -d
```
- App: http://localhost:80

## Without Docker

### Backend
```bash
cd backend
uv venv
uv run python manage.py migrate
uv run python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Services
| Service      | Port  | Description          |
|-------------|-------|----------------------|
| backend     | 8000  | Django REST API      |
| frontend    | 3000  | React + Vite         |
| db          | 5432  | PostgreSQL           |
| redis       | 6379  | Celery broker        |
| celery      | -     | Task worker          |
| celery-beat | -     | Scheduled tasks      |
