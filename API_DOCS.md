# PyDocAI API Documentation

PyDocAI exposes three API surfaces: the **Django REST API** (core orchestration), the **Parser Service** (AST analysis), and the **AI Service** (documentation generation). All services are proxied through Nginx on port `8080` during local development.

## Interactive Docs

When running via Docker Compose, Swagger UI and ReDoc are available at:

| Service | Swagger UI | ReDoc |
|---------|-----------|-------|
| **Django Core API** | `http://localhost:8080/api/docs/` | `http://localhost:8080/api/redoc/` |
| **Parser Service** (FastAPI) | `http://localhost:8080/parser/docs/` | — |
| **AI Service** (FastAPI) | `http://localhost:8080/ai/docs/` | — |

## Authentication

Most endpoints require JWT authentication. Obtain a token pair via:

### Register
```bash
POST /api/users/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123",
  "name": "User Name"
}
```

### Login
```bash
POST /api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepass123"
}
```

Response:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
```

Include the access token in subsequent requests:
```
Authorization: Bearer <access_token>
```

### GitHub OAuth
```bash
POST /api/users/github/login/
Content-Type: application/json

{
  "code": "<github_oauth_code>"
}
```

## Endpoints

### Authentication & Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register/` | Register a new user |
| POST | `/api/users/login/` | Login, returns JWT pair |
| POST | `/api/users/token/refresh/` | Refresh access token |
| GET/PUT | `/api/users/profile/` | Get or update authenticated user's profile |
| POST | `/api/users/password/reset/` | Request password reset email |
| POST | `/api/users/password/reset/confirm/` | Confirm password reset with token |
| POST | `/api/users/github/login/` | GitHub OAuth login |

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List authenticated user's projects |
| POST | `/api/projects/` | Create a new project |
| GET | `/api/projects/{id}/` | Get project detail |
| PUT | `/api/projects/{id}/` | Update project |
| DELETE | `/api/projects/{id}/` | Delete project |
| POST | `/api/projects/{id}/publish/` | Toggle publish status |

### Code Parsing (Python AST)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/parser/analyze-file/` | Analyze a single `.py` file |
| POST | `/api/parser/analyze-folder/` | Analyze a `.zip` archive of Python files |

These endpoints upload the file(s) to the Django API, which forwards them to the **FastAPI Parser** service internally. The parser extracts:
- **Schema tables** — Django model fields, types, constraints, relationships
- **Endpoint mappings** — URL routes, HTTP methods, path parameters, serializer fields

### AI Documentation Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/generate/` | Start AI documentation generation for a project |
| GET | `/api/ai/status/{task_id}/` | Poll generation status |

The generation flow:
1. POST to `/api/ai/generate/` with a `project_id` — returns a `task_id`
2. The Django API dispatches the task to the **FastAPI AI** service
3. The AI service uses **Groq** (primary), **Gemini**, or **Claude** (fallbacks) to generate documentation
4. Poll `/api/ai/status/{task_id}/` until `status` is `completed`
5. Retrieve the generated docs from the project detail endpoint

### Universal Code Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/universal/analyze/` | Analyze code in any supported language |
| GET | `/api/universal/status/{id}/` | Poll analysis status |

Works with Python, JavaScript, TypeScript, Java, Go, Rust, and more. Unlike AST mode, universal mode sends code directly to the AI for analysis without pre-parsing.

### GitHub Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/github/repos/` | List authenticated user's GitHub repositories |
| POST | `/api/github/fetch/` | Fetch repository contents for analysis |

### Exports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/exports/markdown/{id}/` | Export project documentation as Markdown |

### Comments (Public Docs)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/comments/` | List comments on a published doc |
| POST | `/api/comments/` | Create a comment |
| DELETE | `/api/comments/{id}/` | Delete own comment |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/feedback/` | List user's feedback submissions |
| POST | `/api/feedback/` | Submit feedback |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | List authenticated user's notifications |

### Public Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/public/projects/` | List all published projects (no auth required) |
| GET | `/api/public/projects/{slug}/` | Get a published project by slug (no auth required) |

### Admin Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin-dashboard/stats/` | Admin dashboard statistics (admin only) |

## FastAPI Microservice Endpoints

These endpoints are not intended for direct external use — they are called internally by the Django API.

### Parser Service (`/parser/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/parser/analyze-file/` | Parse a single Python file via AST |
| POST | `/parser/analyze-folder/` | Parse a ZIP of Python files via AST |
| GET | `/parser/status/{task_id}/` | Get parsing task status |
| GET | `/parser/health/` | Health check |

### AI Service (`/ai/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/generate-docs/` | Generate documentation via AI |
| GET | `/ai/status/{task_id}/` | Get generation task status |
| GET | `/ai/health/` | Health check |

## Error Responses

All endpoints return consistent error shapes:

```json
{
  "detail": "Human-readable error message"
}
```

Or for validation errors:

```json
{
  "field_name": ["This field is required."]
}
```

Common HTTP status codes:
- `200` — Success
- `201` — Created
- `202` — Accepted (async task dispatched)
- `400` — Bad request / validation error
- `401` — Unauthenticated
- `403` — Forbidden
- `404` — Not found
- `429` — Rate limited
