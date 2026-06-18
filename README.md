<div align="center">

# PyDocAI

### AI-Powered Documentation Generator for Any Language

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/dennisjoseph2025/PyDocAI?style=social)](https://github.com/dennisjoseph2025/PyDocAI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/dennisjoseph2025/PyDocAI?style=social)](https://github.com/dennisjoseph2025/PyDocAI/network/members)
[![Vercel](https://img.shields.io/badge/deployed%20on-Vercel-black?logo=vercel)](https://pydocai.vercel.app)
[![Django](https://img.shields.io/badge/backend-Django-092E20?logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/frontend-React-61DAFB?logo=react)](https://react.dev/)

**Upload your code and let AI generate beautiful, comprehensive documentation in seconds.**

[🌐 Live Demo](https://pydocai.vercel.app) · [🐛 Report Bug](https://github.com/dennisjoseph2025/PyDocAI/issues) · [✨ Feature Request](https://github.com/dennisjoseph2025/PyDocAI/issues)

---

</div>

## Features

- **🤖 AI-Powered Documentation** — Parses your code and generates human-readable docs using Groq AI (with Gemini/Claude fallbacks)
- **🌐 Universal Language Support** — Works with Python, JavaScript, TypeScript, Java, Go, Rust, and more via AI-driven analysis
- **🐍 Python AST Mode** — Deep Python/Django code analysis with AST parsing for schema tables, endpoint mapping, and model relationships
- **📁 Multiple Input Methods** — Upload single `.py` files, `.zip` archives, paste raw code, or connect a GitHub repository
- **📊 Schema Generation** — Auto-compiled tables detailing database models, field types, constraints, and relationships (Python mode)
- **🔗 Endpoint Mapping** — Automated REST API documentation with HTTP methods, path parameters, and JSON responses (Python mode)
- **📝 Markdown Export** — Export documentation as clean Markdown, compatible with GitHub, GitLab, and VS Code
- **📢 Publish & Share** — Publish documentation publicly with shareable links and community comments
- **🔐 User Authentication** — JWT-based auth with GitHub OAuth, email/password registration, password reset
- **📱 Fully Responsive** — Mobile-first dark UI with slide-in sidebar navigation, works on phones, tablets, and desktops

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Vite, TypeScript, Tailwind CSS, React Router |
| **Backend** | Django 5, Django REST Framework, Celery, Redis |
| **Database** | PostgreSQL |
| **AI** | Groq API (LLaMA), Gemini/Claude fallbacks |
| **Deployment** | Vercel (frontend), AWS EC2 + RDS + ElastiCache (backend) |

## Quick Start

### With Docker

```bash
docker-compose up --build -d
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

### Without Docker

**Backend:**

```bash
cd backend
uv venv
uv run python manage.py migrate
uv run python manage.py runserver
```

**Frontend:**

```bash
cd frondend
npm install
npm run dev
```

## How It Works

### Python Mode (AST-powered)
```
1. Upload Code ──▶ 2. AST Parsing ──▶ 3. AI Generation ──▶ 4. Beautiful Docs
     │                    │                   │                    │
  .py / .zip          Python AST          Groq LLM           Markdown + UI
  GitHub repo        extracts types      writes docs         preview + export
```

### Universal Mode (AI-direct)
```
1. Upload Code ──▶ 2. AI Analysis ──▶ 3. Structured Docs
     │                    │                   │
  any language         Groq LLM           Tabbed README /
  (.py/.js/.ts/...)   analyzes code      API / Architecture
```

## Project Structure

```
PyDocAi/
├── backend/                    # Django REST API
│   ├── apps/
│   │   ├── users/             # Auth & user management
│   │   ├── projects/          # Project CRUD
│   │   ├── parser/            # Python AST parsing
│   │   ├── ai/               # AI documentation generation
│   │   ├── universal/        # Universal code analysis
│   │   ├── github_integration/# GitHub OAuth & repo fetching
│   │   ├── exports/          # Markdown export
│   │   ├── comments/         # Public doc comments
│   │   ├── feedback/         # User feedback & ratings
│   │   ├── admin_dashboard/  # Admin panel
│   │   ├── notifications/    # User notifications
│   │   └── internal/         # Internal utilities
│   ├── services/
│   │   ├── parser/           # FastAPI AST parsing service
│   │   └── ai/               # FastAPI AI generation service
│   ├── config/               # Django settings
│   └── requirements/
├── frondend/                  # React + Vite frontend
│   └── src/
│       ├── pages/            # Route pages (19 pages)
│       ├── components/       # Reusable UI components
│       ├── hooks/            # Custom React hooks
│       ├── context/          # Auth context
│       └── api/              # API client
├── docker-compose.yml
├── nginx/
└── README.md
```

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register/` | POST | Register new user |
| `/api/auth/login/` | POST | Login (JWT) |
| `/api/auth/profile/` | GET/PUT | Get/update profile |
| `/api/auth/password/reset/` | POST | Request password reset |
| `/api/auth/github/login/` | POST | GitHub OAuth login |
| `/api/projects/` | GET/POST | List / create projects |
| `/api/projects/{id}/` | GET/PUT/DELETE | Project detail / update / delete |
| `/api/projects/{id}/publish/` | POST | Toggle publish status |
| `/api/parser/analyze-file/` | POST | Analyze single `.py` file (AST) |
| `/api/parser/analyze-folder/` | POST | Analyze ZIP folder (AST) |
| `/api/ai/generate/` | POST | Start AI documentation generation |
| `/api/ai/status/{task_id}/` | GET | Poll generation status |
| `/api/universal/analyze/` | POST | Analyze any code (universal mode) |
| `/api/universal/status/{id}/` | GET | Poll universal analysis status |
| `/api/github/repos/` | GET | List user's GitHub repos |
| `/api/github/fetch/` | POST | Fetch repo contents |
| `/api/exports/markdown/{id}/` | GET | Export as Markdown |
| `/api/comments/` | GET/POST | List / create comments |
| `/api/comments/{id}/` | DELETE | Delete comment |
| `/api/feedback/` | GET/POST | List / submit feedback |
| `/api/notifications/` | GET | List notifications |
| `/api/public/projects/` | GET | List published projects |
| `/api/public/projects/{slug}/` | GET | Get published project detail |
| `/api/admin-dashboard/stats/` | GET | Admin dashboard stats |

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DJANGO_SECRET_KEY` | Django secret key |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL credentials |
| `DB_HOST`, `DB_PORT` | PostgreSQL host and port |
| `CELERY_BROKER_URL` | Redis URL for Celery broker |
| `GROQ_API_KEY` | Primary Groq AI API key |
| `GROQ_API_KEY_2` | Secondary Groq AI API key (fallback) |
| `GITHUB_CLIENT_ID` | GitHub OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth app secret |
| `GITHUB_API_TOKEN` | GitHub API token for repo fetching |
| `EMAIL_HOST`, `EMAIL_PORT` | SMTP server settings |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP credentials |
| `FRONTEND_URL` | Frontend origin for CORS |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key (production) |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key (production) |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name (production) |

### Frontend (`frondend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_GITHUB_CLIENT_ID` | GitHub OAuth client ID for frontend login |

---

## Contributing

We welcome all contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**Ways to help:**
- 🐛 Report bugs via [GitHub Issues](https://github.com/dennisjoseph2025/PyDocAI/issues)
- 💡 Suggest features
- 🔧 Submit pull requests
- ⭐ Star the repo to show support

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<div align="center">

### ⭐ If you find this project useful, give it a star! ⭐

[![GitHub stars](https://img.shields.io/github/stars/dennisjoseph2025/PyDocAI?style=for-the-badge&logo=github)](https://github.com/dennisjoseph2025/PyDocAI/stargazers)

Built with ❤️ for the Python community

</div>
