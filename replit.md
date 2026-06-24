# a4u Resume AI Coaching System

An AI-powered resume coaching and job application management platform. Users can build resumes, receive AI-driven feedback tailored to their career path (IT, Management, General), and track job applications.

## How to Run

The app starts automatically via the **Start application** workflow, which runs:
```
python main.py
```

This initializes the SQLite database (with seed data) and starts Flask on port 5000.

## Project Structure

```
main.py                  # Entry point — adds a4u-webapp to path and starts Flask
a4u-webapp/
  app.py                 # Flask app factory, routes, DB init, session auth
  models.py              # SQLAlchemy models (User, Resume, Template, Application, UploadedFile)
  admin_routes.py        # Admin dashboard API
  resume_routes.py       # Resume CRUD API
  coaching_routes.py     # AI coaching API (OpenAI / Anthropic / mock fallback)
  *.html                 # Frontend pages (served as static files)
  static/                # Avatars and OG images
  uploads/               # User-uploaded resume files (PDF/DOCX)
  a4u.db                 # SQLite database (auto-created)
```

## Default Credentials

- **Admin**: admin@a4u.com / admin1234
- **Demo user**: demo@a4u.com / demo1234

## AI Coaching (Optional)

The coaching feature works in mock/demo mode out of the box. To enable real AI coaching, add one of these secrets in the Replit Secrets tab:

- `OPENAI_API_KEY` — uses GPT-4o-mini
- `ANTHROPIC_API_KEY` — uses Claude 3 Haiku

## Environment Variables

- `SECRET_KEY` — Flask session secret (set automatically)
- `OPENAI_API_KEY` — Optional, for real AI coaching
- `ANTHROPIC_API_KEY` — Optional, for real AI coaching
- `ADMIN_PASSWORD` — Optional, overrides default admin password

## User Preferences

- Keep the Flask app in `a4u-webapp/` and use `main.py` at the root as the entry point
- SQLite is used for persistence; the DB file lives at `a4u-webapp/a4u.db`
