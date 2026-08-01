# DADCARE

**Multi-tenant business super-app for East and Southern Africa.**
Built with Python/Django + PostgreSQL schema-per-tenant + Vanilla JS PWA.

---

## Architecture

```
dadcare.app          → Public marketplace (no login required)
shop.dadcare.app     → Shop mini-app (tenant dashboard)
control.dadcare.app  → Super Admin panel (hidden from public)
```

**Stack:**
- Backend: Python 3.11 / Django 4.2 / Django REST Framework
- Database: PostgreSQL 15 (Neon.tech) — schema-per-tenant isolation
- Frontend: Vanilla HTML/CSS/JS — no framework, PWA
- AI: Google Gemini Flash 2.0 (marketplace moderation)
- Images: Cloudinary (cloud: laa2yvv4)
- Payments: Pi Network SDK + USDT TRC-20
- Hosting: Render.com (backend) + Vercel (frontend) + Neon.tech (DB)

---

## Quick Start (Local)

```bash
# 1. Clone
git clone https://github.com/hmakenzi44-oss/dadcare.git
cd dadcare

# 2. Python environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Environment variables
cp .env.example .env
# Edit .env with your DB credentials and API keys

# 4. Database setup
createdb dadcare_dev
python manage.py migrate
python manage.py setup_dadcare   # seeds mini-apps + audit trigger

# 5. Create Super Admin
python manage.py create_super_admin

# 6. Run
python manage.py runserver
```

Open http://localhost:8000

---

## Project Structure

```
dadcare/
├── apps/
│   ├── auth_app/        GlobalUser, RevokedToken — public schema
│   ├── tenants/         Tenant, BusinessMember, MiniApp, InviteCode
│   ├── shop/            Products, Sales, POS, Orders, HR — tenant schema
│   ├── marketplace/     Public listings — public schema
│   ├── ai_moderation/   Gemini integration + moderation queue
│   ├── super_admin/     SA auth (TOTP), tenant mgmt, payments
│   └── core/            JWT service, audit service, permissions, base models
├── middleware/
│   ├── jwt_middleware.py      Extracts login + business JWT from cookies
│   ├── tenant_middleware.py   Sets search_path = tenant_{uuid} per request
│   └── audit_middleware.py    Thread-local audit context
├── static/
│   ├── css/main.css           Design system (deep indigo + violet + amber)
│   ├── js/app.js              Router, API client, Toast, i18n (SW/EN)
│   ├── js/pages.js            12 SPA page renderers
│   ├── manifest.json          PWA manifest
│   └── sw.js                  Service worker
└── templates/base.html        SPA shell
```

---

## API Reference

| App | Endpoints |
|-----|-----------|
| Auth | 7 — register, login, logout, select-business, profile, update, change-password |
| Tenants | 9 — create, me, members, invite, join, remove-member, permissions, mini-apps |
| Shop | 25 — products, POS sales, void, stock movements, customers, suppliers, purchase orders, wholesale orders, reports, settings |
| Marketplace | 7 — browse (public), categories, detail, submit, mine, update, delete |
| AI Moderation | 3 — queue, manual review, remoderate |
| Super Admin | 21 — auth+TOTP, dashboard, tenants, payments, mini-apps, moderation, audit, users |

**Total: 72 API endpoints**

---

## Multi-Tenancy

Every business gets its own PostgreSQL schema (`tenant_{uuid}`).

```
public schema       → global_users, tenants, business_members, marketplace_listings, audit_log
tenant_{uuid}       → products, sales, customers, suppliers, orders, stock_movements, ...
```

`TenantMiddleware` sets `search_path = tenant_{uuid}` on **every request**.
Schema name validated against `^tenant_[uuid]$` regex — SQL injection impossible.

---

## Auth Flow

```
1. POST /api/auth/login/
   → validates email+password
   → sets dadcare_login_jwt cookie (30 days, httpOnly)
   → returns user + businesses list

2. POST /api/auth/select-business/
   → validates tenant membership + subscription status
   → sets dadcare_business_jwt cookie (8 hours, httpOnly)
   → TenantMiddleware reads this cookie and sets search_path

3. POST /api/auth/select-business/ (again, different tenant_id)
   → switches business WITHOUT logout
   → new business JWT replaces old one
```

---

## AI Moderation

Marketplace listings are scored by Gemini Flash 2.0:

| Score | Action |
|-------|--------|
| >= 85 | `auto_approved` — visible immediately |
| 50–84 | `pending` — manual review queue |
| < 50  | `auto_rejected` — hidden, seller notified |

On API failure: falls back to `pending` — listings never silently lost.

---

## Super Admin

Access: `control.dadcare.app/sa/`

Login is **2-step**:
1. `POST /sa/auth/login/` — email + password → pre-auth token
2. `POST /sa/auth/verify-totp/` — TOTP code → SA JWT (4h, SameSite=Strict)

TOTP setup: `POST /sa/auth/setup-totp/` → QR code → `POST /sa/auth/confirm-totp/`

Create first SA: `python manage.py create_super_admin` (CLI only, no HTTP endpoint)

---

## Deployment (Render.com)

```bash
# render.yaml is pre-configured
# Set these env vars in Render dashboard:
SECRET_KEY=...
DATABASE_URL=postgresql://...   # from Neon.tech
JWT_SECRET=...
GEMINI_API_KEY=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

Post-deploy:
```bash
python manage.py setup_dadcare
python manage.py create_super_admin
```

---

## Trial Period

**90 days — hardcoded in `settings.py` as `TRIAL_DAYS = 90`.**
Never configurable via UI. Super Admin can extend manually per tenant.

---

## Payments

Subscription payments are **manual confirmation**:
1. Tenant submits payment with transaction reference
2. Super Admin sees it in `control.dadcare.app/sa/payments/`
3. SA confirms → subscription extended, tenant status → `active`

Supported: Pi Network + USDT TRC-20

---

## License

Private — DADCARE © 2026 Hojey Abdallah Makenzi
