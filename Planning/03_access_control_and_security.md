# 03 – Access Control & Security

## Authentication

Users register through a **single registration form** with a role dropdown
(Reader, Journalist, Editor). The role is saved directly to the `CustomUser`
model. There are no separate registration pages or forms per role.

Login uses Django's built-in `authenticate()` and `login()` functions. After a
successful login, users are redirected based on their role:

- **Journalist** → journalist dashboard (`/journalist/dashboard/`)
- **Editor** → editor queue (`/editor/queue/`)
- **Reader** → article list (`/`)

Logout calls Django's `logout()`, clears the session, and redirects to the
login page.

A **password reset** flow is available using Django's built-in views
(`PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`,
`PasswordResetCompleteView`). During development, reset emails are printed to
the console via `django.core.mail.backends.console.EmailBackend`. In production,
an SMTP backend is configured via `.env`. The reset link expires after 15
minutes (`PASSWORD_RESET_TIMEOUT = 900`).

---

## Django Groups & Signals

Three Django groups — **Reader**, **Journalist**, and **Editor** — are created
via a data migration (`0002_create_groups`). A `post_save` signal on
`CustomUser` automatically assigns the user to the matching group and removes
them from any other role groups on every save. This keeps group membership in
sync with the `role` field without manual admin intervention.

### Group Permissions

| Group | Permissions assigned |
|-------|----------------------|
| **Reader** | `view_article`, `view_newsletter` |
| **Journalist** | `add_article`, `view_article`, `change_article`, `delete_article`, `add_newsletter`, `view_newsletter`, `change_newsletter`, `delete_newsletter` |
| **Editor** | `view_article`, `change_article`, `delete_article`, `view_newsletter`, `change_newsletter`, `delete_newsletter` |

---

## Role-Based Access Control

Access is enforced at three levels:

### 1. Custom Role Decorators (`news/decorators.py`)

Three decorators — `@journalist_required`, `@editor_required`,
`@reader_required` — enforce role-based access and support three roles:

- If the user is **not authenticated**, the decorator redirects to the login
  page (`accounts:login`).
- If the user is authenticated but has the **wrong role**, the decorator returns
  HTTP 403 Forbidden, rendered from `templates/403.html`.

### 2. Object-Level Checks in Views

- Journalist views use `get_object_or_404(Article, id=article_id, author=request.user)`
  to ensure a journalist can only edit or delete their own articles.
- This returns a 404 rather than a 403, which avoids confirming whether the
  resource exists to an unauthorised user.

### 3. DRF Permission Classes (API layer, `news/permissions.py`)

Four custom DRF permission classes enforce role restrictions on every API
endpoint:

| Class | Rule |
|-------|------|
| `IsJournalist` | `request.user.role == 'journalist'` |
| `IsEditor` | `request.user.role == 'editor'` |
| `IsReader` | `request.user.role == 'reader'` |
| `IsAuthorOrEditor` | Object-level: `obj.author == request.user` OR `role == 'editor'` |

---

## Access Matrix

| Resource / Action | Guest | Reader | Journalist | Editor | Admin |
|-------------------|-------|--------|------------|--------|-------|
| View article list | ✓ | ✓ | ✓ | ✓ | ✓ |
| View article detail | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create article | ✗ | ✗ | ✓ (own) | ✗ | ✓ |
| Edit article | ✗ | ✗ | ✓ (own) | ✓ (any) | ✓ |
| Delete article | ✗ | ✗ | ✓ (own) | ✓ (any) | ✓ |
| Approve article | ✗ | ✗ | ✗ | ✓ | ✓ |
| View newsletters | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create newsletter | ✗ | ✗ | ✓ (own) | ✗ | ✓ |
| Edit newsletter | ✗ | ✗ | ✓ (own) | ✓ (any) | ✓ |
| Subscribe to publisher/journalist | ✗ | ✓ | ✗ | ✗ | ✓ |
| Editor queue | ✗ | ✗ | ✗ | ✓ | ✓ |
| API: GET /api/articles/ | ✗ | ✓ | ✓ | ✓ | ✓ |
| API: POST /api/articles/ | ✗ | ✗ | ✓ | ✗ | ✓ |
| API: PATCH approved=True | ✗ | ✗ | ✗ | ✓ | ✓ |
| API: GET /api/articles/subscribed/ | ✗ | ✓ | ✗ | ✗ | ✓ |
| Django admin | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Password Policy

Django's default password validators are enabled:

- Cannot be too similar to the username or email.
- Minimum 8 characters.
- Cannot be a commonly used password.
- Cannot be entirely numeric.

Passwords are hashed using PBKDF2 with SHA256 — never stored as plain text.

---

## Security Practices

| Practice | Implementation |
|----------|----------------|
| Secret key & credentials | Stored in `.env`, loaded via `python-decouple`, never committed to version control |
| CSRF protection | Django's `CsrfViewMiddleware` is enabled; all forms include `{% csrf_token %}` |
| Session security | Sessions stored server-side in the database; browser only holds a session cookie ID |
| Email uniqueness | Enforced at the model level (`unique=True`) and validated again in `clean_email()` to produce user-friendly error messages |
| Twitter credentials | Loaded from `.env`; `TwitterService` logs a warning and disables tweeting gracefully if credentials are absent |
| X-Frame-Options | Django's `XFrameOptionsMiddleware` is enabled (clickjacking protection) |
| Debug mode | `DEBUG=False` in production; controlled via `.env` |
