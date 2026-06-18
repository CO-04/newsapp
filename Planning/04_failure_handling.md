# 04 – Failure Handling & Recovery

## Purpose

This document covers the failure scenarios that can occur in the application
and how the system should respond to or recover from each one.

---

## User Input Failures

### Registration

If a user submits the registration form with missing required fields, Django's
form validation rejects the submission and re-renders the form with field-level
error messages.

If the chosen **username already exists**, the `AbstractUser` model enforces
uniqueness at the database level and the form displays an appropriate error.

If the chosen **email already exists**, the `clean_email()` method on
`RegistrationForm` raises a `ValidationError` before the user is saved:

```python
def clean_email(self):
    email = self.cleaned_data['email'].lower()
    if CustomUser.objects.filter(email=email).exists():
        raise forms.ValidationError(
            'An account with this email address already exists.'
        )
    return email
```

If the **password fails** any validator (too short, too common, too similar to
username), the form re-renders with the validator's error message.

### Login

If an incorrect username or password is provided, `authenticate()` returns
`None` and the login page re-renders with a generic "Invalid username or
password." message. The error does not reveal whether the username or the
password was wrong, to avoid username enumeration.

### Article Form

If a journalist submits the article form with a missing title or empty content,
`ArticleForm` validation catches it and re-renders with field errors. An
uploaded non-image file is rejected by Django's `ImageField` validation (backed
by Pillow).

### Newsletter Form

If a journalist submits without a title, `NewsletterForm` validation catches it.
The article multi-select is optional, so an empty newsletter is allowed and can
have articles added later.

---

## Permission Failures

| Scenario | System response |
|----------|-----------------|
| Guest accesses a protected page | Decorator redirects to `accounts:login` with `?next=` parameter |
| User accesses a page for a different role | Decorator returns HTTP 403, rendered from `403.html` |
| Journalist tries to edit another journalist's article | `get_object_or_404(Article, id=..., author=request.user)` returns 404, avoiding confirmation the article exists |
| Reader attempts to access editor queue | `@editor_required` returns 403 |
| API request with missing/invalid JWT token | DRF returns `401 Unauthorized` with JSON error body |
| API request from correct role but wrong object ownership | `IsAuthorOrEditor` returns `403 Forbidden` |

---

## Data Integrity

### Article Approval Re-trigger

The `post_save` signal on `Article` uses a `_just_approved` flag set in the
approve view. This prevents the email and tweet from firing every time the
article is edited after approval:

```python
# In the approve view:
article._just_approved = True
article.save()

# In the signal:
if not getattr(instance, '_just_approved', False):
    return
```

If the article is later edited by an editor (without re-approval), the flag is
absent and the signal exits early — no duplicate emails or tweets are sent.

### Article Not Found

All detail, edit, delete, and approve views use `get_object_or_404()`. If an
article ID does not exist, Django returns a 404 page rather than a 500 error.

### Publisher Deleted

`Article.publisher` uses `on_delete=models.SET_NULL`. If a publisher is
deleted, affected articles become independent (no publisher) without being
deleted. Their existing approval state is preserved.

---

## Notification Failures

### Email Sending Fails

`send_approval_emails()` in `news/utils.py` is called from the signal. If
`send_mail()` raises an `SMTPException` or any other exception, it is caught
and logged at `ERROR` level. The article approval is not rolled back — the
article remains approved and the page does not error out for the editor.

```python
try:
    send_mail(subject, message, from_email, recipient_list)
except Exception as exc:
    logger.error('Failed to send approval email: %s', exc)
```

### Twitter API Fails

`TwitterService.tweet()` wraps the API call in a try/except. If credentials
are missing or the API returns an error, a warning is logged and the method
returns `None` silently. The article approval page does not show an error to
the editor.

```python
try:
    response = self.oauth.post(TWEET_URL, json={'text': text})
    response.raise_for_status()
except Exception as exc:
    logger.warning('Tweet failed: %s', exc)
    return None
```

### Missing Twitter Credentials

`TwitterService._build_oauth()` checks that all four credential settings are
non-empty. If any are missing, it logs a warning and sets `self.oauth = None`.
All subsequent `tweet()` calls return `None` immediately without making a
network request.

---

## API Failure Responses

All API errors return JSON with a descriptive message. DRF's default exception
handler is used without modification.

| Scenario | HTTP Status | Response body |
|----------|-------------|---------------|
| Missing/expired JWT token | 401 | `{"detail": "Authentication credentials were not provided."}` |
| Valid token but wrong role | 403 | `{"detail": "You do not have permission to perform this action."}` |
| Article not found | 404 | `{"detail": "Not found."}` |
| Invalid POST data | 400 | Field-level validation errors as JSON |
| Reader tries to POST article | 403 | Permission denied |
| Journalist tries to set `approved=True` | 400/403 | `approved` field is read-only or permission denied |
