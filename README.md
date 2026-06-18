# NewsApp

A Django news platform where journalists write articles, editors approve them, and readers subscribe to follow content they care about.

---

## Tech Stack

- **Python 3.13 / Django 6.0.5**
- **MySQL 8** (primary database; compatible with MariaDB; SQLite used automatically when running tests)
- **Django REST Framework + SimpleJWT** (REST API with JWT authentication)
- **Bootstrap 5** (server-rendered templates, no JS framework)
- **python-decouple** (secrets loaded from `.env`)
- **requests-oauthlib** (OAuth1 session for X / Twitter v2 API)
- **flake8** (PEP 8 linting — 0 violations, configured via `setup.cfg`)

---

## Roles

| Role | What they can do |
|---|---|
| **Reader** | Browse articles and newsletters, subscribe to journalists and publishers, receive email alerts on approval |
| **Journalist** | Write articles (save as draft or submit for review), create newsletters from approved articles |
| **Editor** | Review submitted articles, approve or reject them, create and manage publishers |
| **Superuser / Admin** | Full access to the Django admin panel |

---

## The Main Flow

1. A **journalist** writes an article and either **Save Draft** (stays private) or **Submit for Review** (enters the editor queue).
2. An **editor** opens the review queue — only submitted articles appear — and clicks **Approve** or **Reject**.
3. Approved articles go live on the public list.
4. Subscribed **readers** receive an email notification automatically.
5. Optionally, a tweet (with the article image if one exists) is posted to X / Twitter.

---

## Features

- **Accounts** — Register as any role, log in, log out, reset password via email token.
- **Draft / Submit workflow** — Editors only see articles the journalist has explicitly submitted; unfinished drafts stay private.
- **Articles** — Full CRUD with image upload; unapproved articles are hidden from the public.
- **Newsletters** — Journalists bundle approved articles into newsletters.
- **Publishers** — Named publishers (e.g. news outlets) can be attached to articles; editors manage publishers.
- **Subscriptions** — Subscribe / unsubscribe buttons on article detail and publisher detail pages; toggle state shown in real time.
- **Email notifications** — Sent on article approval to all subscribers; deduplication prevents double emails if a reader follows both the journalist and their publisher.
- **X / Twitter integration** — Singleton `TwitterService` posts a tweet with optional image on approval; missing credentials disable tweeting gracefully without breaking the workflow.
- **REST API** — Full CRUD over JSON, secured with Bearer JWT tokens.
- **Admin panel** — ⚙ Admin Panel button in the navbar for superusers.
- **Unit tests** — 33 automated tests covering models, views, decorators, signals (mocked), and API endpoints.

---

## Project Structure

```
newsapp/
├── manage.py
├── requirements.txt
├── setup.cfg               # flake8 config
├── .env.example            # template — copy to .env
├── newsapp/                # Project config (settings, root URLs)
├── accounts/               # CustomUser model, registration, login, password reset
├── news/                   # Articles, newsletters, publishers, subscriptions, API
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── api_views.py
│   ├── api_urls.py
│   ├── serializers.py
│   ├── permissions.py
│   ├── forms.py
│   ├── signals.py
│   ├── utils.py            # email + tweet helpers
│   ├── twitter.py          # TwitterService singleton
│   └── templates/news/
├── templates/              # Shared templates (base.html, 403.html)
└── media/                  # Uploaded article images
```

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=newsapp_db
DB_USER=newsapp_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=3306

# Optional — leave blank to disable tweeting
TWITTER_API_KEY=
TWITTER_API_KEY_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
```

### 4. Create the MySQL database and user

```sql
CREATE DATABASE newsapp_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'newsapp_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON newsapp_db.* TO 'newsapp_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`

---

## Running Tests

Tests use an in-memory SQLite database automatically — no MySQL credentials needed:

```bash
python manage.py test accounts news
```

---

## Key URLs

### Web

| URL | Description | Access |
|---|---|---|
| `/` | Public article list | Everyone |
| `/articles/create/` | Write a new article | Journalist |
| `/articles/<id>/` | Article detail | Everyone (approved only for public) |
| `/articles/<id>/edit/` | Edit article | Author or Editor |
| `/articles/<id>/delete/` | Delete article | Author or Editor |
| `/articles/<id>/approve/` | Approve article | Editor |
| `/articles/<id>/reject/` | Reject article | Editor |
| `/editor/queue/` | Submitted articles awaiting review | Editor |
| `/journalist/dashboard/` | Journalist's own articles | Journalist |
| `/newsletters/` | Newsletter list | Everyone |
| `/newsletters/create/` | Create newsletter | Journalist |
| `/newsletters/<id>/` | Newsletter detail | Everyone |
| `/publishers/create/` | Create publisher | Editor |
| `/publishers/<id>/` | Publisher detail + subscribe | Everyone |
| `/journalists/<id>/` | Journalist profile + subscribe | Everyone |
| `/subscribe/publisher/<id>/` | Toggle publisher subscription | Reader |
| `/subscribe/journalist/<id>/` | Toggle journalist subscription | Reader |
| `/accounts/register/` | Register | Public |
| `/accounts/login/` | Login | Public |
| `/accounts/logout/` | Logout | Authenticated |
| `/accounts/password-reset/` | Password reset | Public |
| `/admin/` | Django admin panel | Superuser |

### REST API (`/api/`)

All write endpoints require `Authorization: Bearer <access_token>`.

| Method | URL | Description |
|---|---|---|
| `POST` | `/api/token/` | Obtain JWT access + refresh tokens |
| `POST` | `/api/token/refresh/` | Refresh access token |
| `GET` | `/api/publishers/` | List all publishers |
| `POST` | `/api/publishers/` | Create publisher (Editor only) |
| `GET/PUT/PATCH/DELETE` | `/api/publishers/<id>/` | Publisher detail |
| `GET` | `/api/articles/` | List articles (filtered by role) |
| `POST` | `/api/articles/` | Create article (Journalist only) |
| `GET/PUT/PATCH/DELETE` | `/api/articles/<id>/` | Article detail |
| `PATCH` | `/api/articles/<id>/approve/` | Approve article (Editor only) |
| `GET` | `/api/newsletters/` | List newsletters |
| `POST` | `/api/newsletters/` | Create newsletter (Journalist only) |
| `GET/PUT/PATCH/DELETE` | `/api/newsletters/<id>/` | Newsletter detail |

#### Example — obtain a token

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
     -H "Content-Type: application/json" \
     -d '{"username": "Journalist1", "password": "Wr!ter1_Journ@l!st"}'
```

Response:
```json
{
  "access":  "<60-minute token>",
  "refresh": "<7-day token>"
}
```

Use the access token in subsequent requests:
```bash
curl http://127.0.0.1:8000/api/articles/ \
     -H "Authorization: Bearer <access>"
```

---

## Email

All emails (article approval notifications, password reset) are printed to the console during development:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

For production, switch to an SMTP backend and set `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, and `EMAIL_HOST_PASSWORD` in `.env`.

---

## Security Notes

- `SECRET_KEY` is loaded from `.env` via python-decouple — never hard-coded
- `DEBUG=True` in development — set to `False` in production
- All forms include `{% csrf_token %}`
- Role-based access is enforced by `@journalist_required`, `@editor_required`, and `@reader_required` decorators (return HTTP 403 for wrong-role users)
- Object-level ownership checks prevent journalists from editing each other's articles
- Django ORM is used for all queries — no raw SQL
- `X-Frame-Options: DENY` is set via `XFrameOptionsMiddleware`
