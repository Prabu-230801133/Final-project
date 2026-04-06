"""
accounts/pipeline.py
Custom social-auth pipeline steps.
"""
from social_core.exceptions import AuthForbidden


def require_pre_registration(backend, details, user=None, *args, **kwargs):
    """
    Block Google OAuth login for emails NOT already registered by admin.

    If the email IS pre-registered, link that existing account to Google
    instead of creating a duplicate user.

    Must be placed BEFORE 'social_core.pipeline.user.create_user'
    in SOCIAL_AUTH_PIPELINE.
    """
    # User already found via social association — allow through
    if user:
        return

    email = details.get('email', '').lower().strip()

    if not email:
        raise AuthForbidden(backend)

    from accounts.models import CustomUser
    try:
        # Email is already registered — link this Google account to it
        existing_user = CustomUser.objects.get(email__iexact=email)
        return {'user': existing_user}
    except CustomUser.DoesNotExist:
        # Not registered — block login entirely
        raise AuthForbidden(backend)


def set_student_role(backend, user, response, *args, **kwargs):
    """
    Called after user is retrieved via social auth.
    Ensures OAuth users get the 'student' role if none is set.
    """
    if user and (not user.role or user.role == ''):
        user.role = 'student'
        user.save(update_fields=['role'])
