"""
accounts.views
==============

HTTP view functions for the NewsApp accounts module.

Views
-----
register
    User registration form; logs in and redirects on success.
login_user
    Authentication form; redirects to role-appropriate page on success.
logout_user
    Logs out the current user and redirects to the article list.
_role_redirect
    Internal helper; returns a redirect based on the user's role.
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    """Handle user registration for all roles via a single form.

    Authenticated users are redirected away immediately. On successful
    registration the user is logged in and redirected to their
    role-appropriate landing page.

    :param request: The incoming HTTP request.
    :type request: HttpRequest
    :returns: Rendered registration form on GET/invalid POST,
        or redirect on success.
    :rtype: HttpResponse
    """
    if request.user.is_authenticated:
        return redirect('news:article_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome, {user.username}! Your account has been created.',
            )
            return _role_redirect(user)
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_user(request):
    """Authenticate and log in a user.

    On success, redirect to the role-appropriate landing page.
    On failure, display an error message and re-render the login form.
    Authenticated users are redirected away immediately.

    :param request: The incoming HTTP request.
    :type request: HttpRequest
    :returns: Rendered login form on GET/failed POST,
        or redirect on success.
    :rtype: HttpResponse
    """
    if request.user.is_authenticated:
        return redirect('news:article_list')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return _role_redirect(user)
        messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_user(request):
    """Log out the current user and redirect to the article list.

    Accepts both GET and POST so a simple link or a form button work.

    :param request: The incoming HTTP request.
    :type request: HttpRequest
    :returns: Redirect to the article list.
    :rtype: HttpResponseRedirect
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('news:article_list')


def _role_redirect(user):
    """Return a redirect to the role-appropriate landing page.

    :param user: The authenticated user whose role determines the target.
    :type user: CustomUser
    :returns: Redirect to the journalist dashboard, editor queue,
        or article list depending on the user's role.
    :rtype: HttpResponseRedirect
    """
    if user.is_journalist():
        return redirect('news:journalist_dashboard')
    if user.is_editor():
        return redirect('news:editor_queue')
    return redirect('news:article_list')
