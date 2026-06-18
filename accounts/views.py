from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def register(request):
    """
    Handle user registration for all roles via a single form.

    On success, log the user in and redirect based on their role:
    - Journalist → journalist dashboard
    - Editor     → editor review queue
    - Reader     → article list (home)
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
    """
    Authenticate and log in a user.

    On success, redirect based on role (same logic as register).
    On failure, display an error message and re-render the login form.
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
    """
    Log out the current user and redirect to the article list.

    Accepts GET and POST so a simple link or a form button both work.
    """
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('news:article_list')


def _role_redirect(user):
    """
    Return an HttpResponseRedirect to the appropriate landing page for the
    given user based on their role.
    """
    if user.is_journalist():
        return redirect('news:journalist_dashboard')
    if user.is_editor():
        return redirect('news:editor_queue')
    return redirect('news:article_list')
