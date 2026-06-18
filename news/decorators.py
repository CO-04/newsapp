"""
Role-based access decorators for news app views.

Three decorators enforce role access at the view level:
- journalist_required : authenticated users with role='journalist'
- editor_required     : authenticated users with role='editor'
- reader_required     : authenticated users with role='reader'

A fourth helper decorator (login_required_custom) is used for views that
perform their own object-level permission checks internally (e.g. edit/delete
where both the author and editors have access).
"""

from functools import wraps

from django.conf import settings
from django.shortcuts import redirect, render


def journalist_required(view_func):
    """
    Restrict the decorated view to users with the Journalist role.

    Authenticated only; anonymous users are redirected to login.
    Authenticated users with a different role receive a 403 response.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Enforce journalist role before calling the wrapped view."""
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_journalist():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def editor_required(view_func):
    """
    Restrict the decorated view to authenticated users with the Editor role.

    Anonymous users are redirected to the login page.
    Authenticated users with a different role receive a 403 response.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Enforce editor role before calling the wrapped view."""
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_editor():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def reader_required(view_func):
    """
    Restrict the decorated view to authenticated users with the Reader role.

    Anonymous users are redirected to the login page.
    Authenticated users with a different role receive a 403 response.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Enforce reader role before calling the wrapped view."""
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_reader():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_custom(view_func):
    """
    Require the user to be authenticated.

    Used for views that perform their own object-level role checks internally
    (e.g. edit/delete where the article author and editors are permitted).
    Anonymous users are redirected to the login page.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Redirect anonymous users to the login page."""
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper
