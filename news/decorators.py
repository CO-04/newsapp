"""
news.decorators
===============

Role-based access-control decorators for NewsApp views.

Decorators
----------
journalist_required
    Restrict a view to authenticated users with ``role='journalist'``.
editor_required
    Restrict a view to authenticated users with ``role='editor'``.
reader_required
    Restrict a view to authenticated users with ``role='reader'``.
login_required_custom
    Require authentication only; object-level role checks are handled
    inside the view itself.
"""

from functools import wraps

from django.conf import settings
from django.shortcuts import redirect, render


def journalist_required(view_func):
    """Restrict the decorated view to users with the Journalist role.

    Anonymous users are redirected to the login page.
    Authenticated users with a different role receive a 403 response.

    :param view_func: The view function to wrap.
    :type view_func: callable
    :returns: The wrapped view enforcing journalist-only access.
    :rtype: callable
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Enforce journalist role before calling the wrapped view.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param args: Positional arguments forwarded to the view.
        :param kwargs: Keyword arguments forwarded to the view.
        :returns: Redirect, 403 response, or the original view response.
        :rtype: HttpResponse
        """
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_journalist():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def editor_required(view_func):
    """Restrict the decorated view to users with the Editor role.

    Anonymous users are redirected to the login page.
    Authenticated users with a different role receive a 403 response.

    :param view_func: The view function to wrap.
    :type view_func: callable
    :returns: The wrapped view enforcing editor-only access.
    :rtype: callable
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Enforce editor role before calling the wrapped view.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param args: Positional arguments forwarded to the view.
        :param kwargs: Keyword arguments forwarded to the view.
        :returns: Redirect, 403 response, or the original view response.
        :rtype: HttpResponse
        """
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_editor():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def reader_required(view_func):
    """Restrict the decorated view to users with the Reader role.

    Anonymous users are redirected to the login page.
    Authenticated users with a different role receive a 403 response.

    :param view_func: The view function to wrap.
    :type view_func: callable
    :returns: The wrapped view enforcing reader-only access.
    :rtype: callable
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Enforce reader role before calling the wrapped view.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param args: Positional arguments forwarded to the view.
        :param kwargs: Keyword arguments forwarded to the view.
        :returns: Redirect, 403 response, or the original view response.
        :rtype: HttpResponse
        """
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        if not request.user.is_reader():
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def login_required_custom(view_func):
    """Require the user to be authenticated.

    Used for views that perform their own object-level role checks
    internally (e.g. edit/delete where the article author and editors
    are both permitted). Anonymous users are redirected to the login
    page.

    :param view_func: The view function to wrap.
    :type view_func: callable
    :returns: The wrapped view enforcing authentication.
    :rtype: callable
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        """Redirect anonymous users to the login page.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param args: Positional arguments forwarded to the view.
        :param kwargs: Keyword arguments forwarded to the view.
        :returns: Redirect to login, or the original view response.
        :rtype: HttpResponse
        """
        if not request.user.is_authenticated:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper
