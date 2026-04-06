"""
accounts/views.py
Login, logout, and role-based redirect views.
Google OAuth is handled by social_django automatically.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Unified login page supporting username/password and Google OAuth.
    Handles google_error query param set by social-auth on AuthForbidden.
    """
    if request.user.is_authenticated:
        return redirect('accounts:redirect')

    # Handle Google OAuth error redirect (set via SOCIAL_AUTH_LOGIN_ERROR_URL)
    google_error = request.GET.get('google_error')
    if google_error == 'not_registered':
        messages.error(
            request,
            '⚠️ Your Google account is not registered in this system. '
            'Please use the credentials provided by your administrator.'
        )

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('accounts:redirect')
            else:
                messages.error(request, 'Your account is disabled. Contact admin.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')



@login_required
def redirect_view(request):
    """
    Redirect user to appropriate dashboard based on role.
    Called after both traditional login and Google OAuth login.
    """
    user = request.user
    if user.is_superuser or user.role == 'django_admin':
        return redirect('/django-admin/')
    elif user.role == 'web_admin':
        return redirect('web_admin:dashboard')
    else:
        # Default: student dashboard
        return redirect('voting:student_dashboard')


def logout_view(request):
    """Log out and redirect to home."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
