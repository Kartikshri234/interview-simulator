# 🎯 AI Interview Simulator

A full-stack Django application that helps candidates practise technical interviews with AI-powered question generation, answer evaluation, resume screening, and performance analytics.

---

## 📁 Project Structure

```
interview_simulator/
├── apps/
│   ├── interview/           # Core interview engine
│   │   ├── models.py        # InterviewSession, InterviewAnswer, QuestionBank, BookmarkedQuestion
│   │   ├── views.py         # HTML page views (dashboard, room, results, history, bookmarks)
│   │   ├── api_views.py     # REST API views (session CRUD, submit answer, voice, facial)
│   │   ├── ai_services.py   # OpenAI: question generation, evaluation, summary; TextBlob sentiment
│   │   ├── urls.py          # HTML URL patterns
│   │   ├── api_urls.py      # REST API URL patterns
│   │   ├── routing.py       # Django Channels WebSocket routing
│   │   └── migrations/      # Database migrations
│   │
│   ├── users/               # Authentication & profiles
│   │   ├── models.py        # CustomUser (email login, daily streak)
│   │   ├── views.py         # HTML login, register, logout, profile
│   │   ├── api_views.py     # REST register, profile, logout, change-password, stats
│   │   ├── jwt_utils.py     # Custom JWT serializer (username OR email login)
│   │   ├── admin.py         # Django admin registration
│   │   ├── urls.py          # HTML URL patterns
│   │   ├── api_urls.py      # REST API URL patterns
│   │   └── migrations/      # Database migrations
│   │
│   └── resume_screening/    # AI resume screening
│       ├── views.py         # Upload form + results view
│       ├── services.py      # PDF/DOCX text extraction, TF-IDF similarity, Claude AI analysis
│       ├── urls.py          # URL patterns
│       └── migrations/      # Database migrations (empty — no models)
│
├── config/                  # Django project configuration
│   ├── settings.py          # All settings (reads from .env)
│   ├── urls.py              # Root URL configuration
│   ├── asgi.py              # ASGI + Channels setup
│   └── wsgi.py              # WSGI for production
│
├── templates/               # Django HTML templates
│   ├── base.html
│   ├── interview/           # dashboard, room, results, history, bookmarks, new_interview
│   ├── users/               # login, register, profile
│   └── resume_screening/    # screening
│
├── static/                  # Source static files (committed to Git)
│   ├── css/                 # app.css, features.css
│   └── js/                  # dashboard.js, interview_room.js, results.js, …
│
├── manage.py
├── requirements.txt
├── build.sh                 # Render.com build script
├── .env.example             # Copy to .env and fill in secrets
├── .gitignore
└── README.md
```

---

## ⚡ Quick Start (Local Development)

### 1. Clone & enter the project
```bash
git clone <your-repo-url>
cd interview_simulator
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env and fill in your SECRET_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Create a superuser (optional — for /admin)
```bash
python manage.py createsuperuser
```

### 7. Collect static files
```bash
python manage.py collectstatic --noinput
```

### 8. Start the development server
```bash
python manage.py runserver
```

Open http://127.0.0.1:8000 — you're live!

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key (50+ random chars) |
| `DEBUG` | ✅ | `True` for dev, `False` for production |
| `ALLOWED_HOSTS` | ✅ | Comma-separated hostnames |
| `OPENAI_API_KEY` | ⭐ | For AI question generation & evaluation |
| `ANTHROPIC_API_KEY` | ⭐ | For AI resume screening (Claude) |
| `DATABASE_URL` | Optional | PostgreSQL URL; defaults to SQLite |
| `REDIS_URL` | Optional | For WebSocket channels; defaults to in-memory |
| `CORS_ALLOWED_ORIGINS` | Optional | Comma-separated allowed origins |

---

## 🚀 Features

| # | Feature |
|---|---|
| 1 | AI-generated interview questions (OpenAI GPT-4o-mini) |
| 2 | Answer evaluation with score, feedback & keyword matching |
| 3 | Sentiment analysis on answers (TextBlob) |
| 4 | Progress charts — score trend & topic breakdown |
| 5 | Session history with detailed per-answer breakdown |
| 6 | Resume screening — TF-IDF similarity + Claude AI analysis |
| 7 | Bookmark questions for focused re-practice |
| 8 | Voice analytics — WPM, filler word detection |
| 9 | Facial emotion analysis (DeepFace — optional) |
| 10 | Mock interview mode (mixed categories) |
| 11 | Smart topic recommendations (based on weak areas) |
| 12 | Adaptive difficulty suggestions |
| 13 | Daily streak tracking |
| 14 | JWT authentication with username OR email login |

---

## 🏗️ Deployment (Render)

The included `build.sh` handles:
1. Installing all dependencies
2. Running `collectstatic`
3. Running `migrate` (only when `DATABASE_URL` is set)

Set these environment variables in the Render dashboard:
- `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=your-domain.onrender.com`
- `DATABASE_URL` (PostgreSQL from Render)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

---

## 🛠️ Tech Stack

- **Backend**: Django 4.2, Django REST Framework, SimpleJWT, Django Channels
- **AI**: OpenAI GPT-4o-mini, Anthropic Claude, TextBlob, DeepFace (optional)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Static files**: WhiteNoise
- **Deployment**: Render / gunicorn
