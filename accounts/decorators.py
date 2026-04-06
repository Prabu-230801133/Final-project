"""
accounts/decorators.py
Custom access control decorators for role-based views.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*roles):
    """
    Decorator that restricts access to views based on user role.
    Usage: @role_required('web_admin', 'django_admin')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access that page.")
                return redirect('accounts:redirect')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def student_required(view_func):
    """Shortcut decorator for student-only views."""
    return role_required('student')(view_func)


def web_admin_required(view_func):
    """Shortcut decorator for web admin-only views."""
    return role_required('web_admin', 'django_admin')(view_func)
