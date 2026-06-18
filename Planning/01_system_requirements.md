# 01 – System Requirements

## Project Overview

This is a news web application built with Django. Users can register as a
**Reader**, **Journalist**, or **Editor**. Readers subscribe to publishers and
journalists and receive approved articles by email. Journalists write articles
and newsletters. Editors review submissions and approve them for publication.
When an article is approved, subscribers are emailed automatically and a tweet
is posted to the designated X (Twitter) account via the Twitter API v2.

The project consists of two Django apps:

- **accounts** — custom user model with three roles, single registration form,
  login/logout, password reset, and group assignment via a `post_save` signal.
- **news** — publishers, articles, newsletters, editor approval queue,
  subscription management, notification signals, and the RESTful API.

---

## Users of the System

| Role | Description |
|------|-------------|
| **Guest** | Unauthenticated visitor. Can view the article list and article details but cannot subscribe, create content, or access the API. |
| **Reader** | Registered user with the Reader role. Can browse all approved articles and newsletters, subscribe/unsubscribe to publishers and journalists, and receive email notifications when subscribed content is approved. |
| **Journalist** | Registered user with the Journalist role. Can create, edit, and delete their own articles and newsletters. May be affiliated with a Publisher. Cannot approve articles. |
| **Editor** | Registered user with the Editor role. Can review unapproved articles in the editor queue and approve or reject them. Can edit or delete any article or newsletter. Cannot create new articles. |
| **Admin** | Django superuser. Manages all data through the admin panel. |

---

## Functional Requirements

### Registration & Authentication

- Any visitor can register using a **single registration form** that includes a
  **role dropdown** (Reader, Journalist, Editor).
- The role is applied to the user on save; no separate registration pages exist.
- `email` is validated for uniqueness at form level and enforced at model level —
  duplicate emails are rejected with a clear error message.
- Users log in with username and password.
- After login, users are redirected based on role:
  - Journalist → journalist dashboard (their article list)
  - Editor → editor article queue
  - Reader → article list (home)
- Logout clears the session and redirects to the login page.
- A password reset flow is available via email using Django's built-in views.
  The reset link expires after 15 minutes. All four reset templates include
  visible submit buttons.
- A `post_save` signal on `CustomUser` assigns the user to the matching Django
  group (Reader, Journalist, or Editor) and removes them from any other role
  groups. Groups and their permissions are created via a data migration.

### Reader Features

- Readers can browse the **article list** (all approved articles, paginated).
- Readers can view any **article detail** page.
- Readers can browse **newsletters**.
- Readers can **subscribe** to a Publisher or a Journalist. Subscription buttons
  appear on publisher/journalist profile pages and redirect back to the same page
  with a flash confirmation message (no loss of browsing context).
- Readers can **unsubscribe** in the same way.
- When an article they have subscribed to is approved, they receive an email with
  the article title, author, and a link to the article.

### Journalist Features

- Journalists can **create** new articles (title, content, image, optional
  publisher affiliation).
- Journalists can **edit** and **delete** their own articles.
- Newly created articles have `approved=False` and are not visible to readers
  until an editor approves them.
- Journalists can **create**, **edit**, and **view** newsletters. A newsletter
  is a curated collection of approved articles.
- Journalists have a **dashboard** listing their submitted articles and
  newsletters, with status indicators (pending / approved).

### Editor Features

- Editors can view the **editor queue** — a list of all unapproved articles.
- Editors can **approve** an article with one click. On approval:
  - The article becomes visible to all readers.
  - Subscribers of the author and the article's publisher (if any) are emailed.
  - A tweet is posted to the designated X account.
- Editors can **reject/un-approve** an article, returning it to pending status.
- Editors can **edit** or **delete** any article or newsletter.

### Admin Features

- The superuser manages all models through Django's admin panel.
- The admin can create publishers and assign journalists/editors to them.

---

## Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Code quality** | All code follows PEP 8. Every class, method, and function has a docstring. Descriptive variable names and good use of whitespace throughout. |
| **Security** | Secrets stored in `.env` (gitignored) and loaded via `python-decouple`. CSRF protection enabled on all forms. Passwords hashed with PBKDF2/SHA256. Role access enforced at decorator and permission level. Object-level checks prevent cross-user data access. |
| **Modularity** | Logic divided into focused functions and classes. No view handles more than one responsibility. |
| **Robustness** | Form validation prevents invalid input. Signals fail gracefully — email/Twitter errors are logged without crashing the request. |
| **Testability** | All business logic is unit-testable. Signals use mocking for email and Twitter in tests. |
| **Database** | MariaDB in production; SQLite used only for test runs (no credentials required). |
| **API** | RESTful JSON API using DRF with JWT authentication. Role-based permission enforcement on every endpoint. |
