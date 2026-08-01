# Push DADCARE to GitHub

## Option A — GitHub.dev (Recommended for Android)

1. Go to: https://github.com/hmakenzi44-oss
2. Create new repo: **dadcare** (private, no README)
3. Open: https://github.dev/hmakenzi44-oss/dadcare
4. In the terminal panel (Ctrl+`):

```bash
# Upload the zip, then:
unzip dadcare-github.zip
git add .
git commit -m "feat: initial DADCARE v1.0 — full stack build"
git push origin main
```

## Option B — Termux (Android)

```bash
pkg install git
git config --global user.name "Hojey Makenzi"
git config --global user.email "your@email.com"

cd /path/to/dadcare
git init
git remote add origin https://github.com/hmakenzi44-oss/dadcare.git
git add .
git commit -m "feat: initial DADCARE v1.0 — full stack build"
git branch -M main
git push -u origin main
```

## Option C — GitHub Desktop (Desktop)

Download zip → extract → open folder in GitHub Desktop → Publish repository

---

## After Push — Deploy to Render.com

1. Connect GitHub repo to Render
2. Set env vars (from .env.example):
   - SECRET_KEY
   - DATABASE_URL (from Neon.tech)
   - JWT_SECRET
   - GEMINI_API_KEY
   - CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET
3. Build command: `pip install -r requirements.txt && python manage.py migrate && python manage.py setup_dadcare`
4. Start command: `gunicorn dadcare.wsgi:application`

## First Run Commands

```bash
python manage.py migrate
python manage.py setup_dadcare
python manage.py create_super_admin
```
