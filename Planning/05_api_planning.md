# 05 – API Planning

## Overview

This document plans the RESTful API for the news application. The API allows
third-party clients to retrieve articles, create content (journalists),
approve articles (editors), and access subscription-filtered content (readers).

---

## 1. Serialisation Format

**JSON** is the primary serialisation format — widely supported, human-readable,
and the DRF default. All responses use `Content-Type: application/json`.

---

## 2. Resources and Fields to Serialise

### `Article`

| Field | Type | Notes |
|-------|------|-------|
| id | integer | Read-only |
| title | string | Required |
| content | string | Required |
| author | string | Username, read-only (`ReadOnlyField`) |
| publisher | integer | Publisher ID (FK), nullable |
| publisher_name | string | Publisher name, read-only (nested) |
| image | string | URL to uploaded image, optional |
| approved | boolean | Read-only for journalists/readers; Editor only can set `True` |
| created_at | datetime | Read-only, ISO 8601 |
| updated_at | datetime | Read-only, ISO 8601 |

### `Newsletter`

| Field | Type | Notes |
|-------|------|-------|
| id | integer | Read-only |
| title | string | Required |
| description | string | Optional |
| author | string | Username, read-only |
| articles | list of integers | Article IDs (M2M) |
| created_at | datetime | Read-only |
| updated_at | datetime | Read-only |

### `Publisher`

| Field | Type | Notes |
|-------|------|-------|
| id | integer | Read-only |
| name | string | Required, unique |
| description | string | Optional |
| website | string | Optional URL |
| created_at | datetime | Read-only |

### `User` (read-only, used in nested representations)

| Field | Type | Notes |
|-------|------|-------|
| id | integer | Read-only |
| username | string | Read-only |
| role | string | Read-only |

---

## 3. API Endpoints

All endpoints are prefixed with `/api/`.

### Authentication (JWT)

| Method | Endpoint | Description | Auth required |
|--------|----------|-------------|---------------|
| POST | `/api/token/` | Obtain JWT access + refresh tokens | No |
| POST | `/api/token/refresh/` | Obtain new access token using refresh token | No (uses refresh token body) |

Credentials posted as JSON: `{"username": "...", "password": "..."}`.

The access token must be sent in the `Authorization` header on all protected
requests:
`Authorization: Bearer <access_token>`

Access tokens expire after **60 minutes**. Clients use the refresh token to
obtain a new access token without re-entering credentials.

---

### Articles

| Method | Endpoint | Description | Auth / Role |
|--------|----------|-------------|-------------|
| GET | `/api/articles/` | List all approved articles | Any authenticated user |
| POST | `/api/articles/` | Create a new article | Journalist (token) |
| GET | `/api/articles/subscribed/` | List approved articles from subscribed publishers/journalists | Reader (token) |
| GET | `/api/articles/<id>/` | Retrieve a single article | Any authenticated user |
| PUT | `/api/articles/<id>/` | Fully update an article | Author (journalist) or Editor |
| PATCH | `/api/articles/<id>/` | Partially update (includes setting `approved=True`) | Author for content fields; Editor only for `approved` |
| DELETE | `/api/articles/<id>/` | Delete an article | Author (journalist) or Editor |

**Business rules:**

- `POST /api/articles/` always creates the article with `approved=False` —
  the serializer forces this regardless of the submitted value.
- Only a user with `role='editor'` can set `approved=True` via PATCH.
- `GET /api/articles/` returns only articles where `approved=True`.
- `GET /api/articles/subscribed/` filters by the reader's
  `subscribed_publishers` and `subscribed_journalists` M2M fields.

---

### Newsletters

| Method | Endpoint | Description | Auth / Role |
|--------|----------|-------------|-------------|
| GET | `/api/newsletters/` | List all newsletters | Any authenticated user |
| POST | `/api/newsletters/` | Create a newsletter | Journalist (token) |
| GET | `/api/newsletters/<id>/` | Retrieve a newsletter with its articles | Any authenticated user |
| PUT | `/api/newsletters/<id>/` | Fully update a newsletter | Author or Editor |
| PATCH | `/api/newsletters/<id>/` | Partially update a newsletter | Author or Editor |
| DELETE | `/api/newsletters/<id>/` | Delete a newsletter | Author or Editor |

---

### Publishers

| Method | Endpoint | Description | Auth / Role |
|--------|----------|-------------|-------------|
| GET | `/api/publishers/` | List all publishers | Any authenticated user |
| GET | `/api/publishers/<id>/` | Retrieve a publisher | Any authenticated user |

Publishers are managed through the Django admin panel and are not
created/edited via the API by regular users.

---

## 4. Permission Class Mapping

| Endpoint | `GET` | `POST` | `PUT` / `PATCH` | `DELETE` |
|----------|-------|--------|-----------------|----------|
| `/api/articles/` | `IsAuthenticated` | `IsJournalist` | — | — |
| `/api/articles/<id>/` | `IsAuthenticated` | — | `IsAuthorOrEditor` | `IsAuthorOrEditor` |
| `/api/articles/subscribed/` | `IsReader` | — | — | — |
| `/api/newsletters/` | `IsAuthenticated` | `IsJournalist` | — | — |
| `/api/newsletters/<id>/` | `IsAuthenticated` | — | `IsAuthorOrEditor` | `IsAuthorOrEditor` |
| `/api/publishers/` | `IsAuthenticated` | — | — | — |

---

## 5. Authentication Flow (Sequence)

```
Client                          Django API
  │                                 │
  │── POST /api/token/ ────────────>│
  │   {"username": "...",           │
  │    "password": "..."}           │
  │                                 │── authenticate() ──> DB
  │                                 │<── user object
  │<── 200 {"access": "...",        │
  │         "refresh": "..."} ──────│
  │                                 │
  │── GET /api/articles/ ──────────>│
  │   Authorization: Bearer <token> │
  │                                 │── validate JWT
  │<── 200 [...articles...] ────────│
  │                                 │
  │  (60 min later — token expired) │
  │                                 │
  │── POST /api/token/refresh/ ────>│
  │   {"refresh": "..."}            │
  │<── 200 {"access": "..."} ───────│
  │                                 │
  │── POST /api/articles/ ─────────>│  (journalist)
  │   Authorization: Bearer <token> │
  │   {"title": "...", ...}         │── IsJournalist check
  │<── 201 {"id": 42, ...} ─────────│
  │                                 │
  │── PATCH /api/articles/42/ ─────>│  (editor)
  │   {"approved": true}            │── IsAuthorOrEditor + role check
  │<── 200 {"approved": true, ...} ─│
  │                                 │── post_save signal fires
  │                                 │── send_approval_emails()
  │                                 │── TwitterService().tweet()
```

---

## 6. Error Response Format

All error responses follow DRF's default JSON structure:

```json
// 401 – not authenticated
{"detail": "Authentication credentials were not provided."}

// 403 – authenticated but wrong role/ownership
{"detail": "You do not have permission to perform this action."}

// 404 – resource not found
{"detail": "Not found."}

// 400 – validation error
{
  "title": ["This field may not be blank."],
  "content": ["This field may not be blank."]
}
```
