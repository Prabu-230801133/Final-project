"""
accounts/views.py
Login, logout, and role-based redirect views.
Google OAuth is handled by social_django automatically.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required


import random
from .models import CustomUser, PasswordResetOTP
from .utils import send_password_reset_otp_email


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


@require_http_methods(["GET", "POST"])
def forgot_password(request):
    """Step 1: Request email and send OTP."""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, 'accounts/forgot_password.html')
            
        user = CustomUser.objects.filter(email=email).first()
        if user:
            # Generate 6-digit OTP
            otp = str(random.randint(100000, 999999))
            PasswordResetOTP.objects.create(user=user, otp=otp)
            
            # Send Email
            if send_password_reset_otp_email(user, otp):
                request.session['reset_email'] = email
                messages.success(request, f"A 6-digit OTP has been sent to {email}.")
                return redirect('accounts:verify_password_otp')
            else:
                messages.error(request, "Failed to send OTP email. Please try again later.")
        else:
            # For security, don't reveal if user exists. 
            # But in this context (college), it's probably fine to be direct.
            messages.error(request, "No account found with that email address.")
            
    return render(request, 'accounts/forgot_password.html')


@require_http_methods(["GET", "POST"])
def verify_password_otp(request):
    """Step 2: Verify the OTP sent to email."""
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:forgot_password')
        
    if request.method == 'POST':
        otp_code = request.POST.get('otp', '').strip()
        user = get_object_or_404(CustomUser, email=email)
        
        # Check latest non-expired, non-verified OTP
        otp_record = PasswordResetOTP.objects.filter(
            user=user, 
            otp=otp_code, 
            is_verified=False
        ).first()
        
        if otp_record and not otp_record.is_expired:
            otp_record.is_verified = True
            otp_record.save()
            request.session['otp_verified'] = True
            messages.success(request, "OTP verified successfully. You can now set a new password.")
            return redirect('accounts:reset_password')
        else:
            messages.error(request, "Invalid or expired OTP code.")
            
    return render(request, 'accounts/verify_password_otp.html', {'email': email})


@require_http_methods(["GET", "POST"])
def reset_password(request):
    """Step 3: Set a new password."""
    email = request.session.get('reset_email')
    is_verified = request.session.get('otp_verified')
    
    if not email or not is_verified:
        messages.error(request, "Session expired or unauthorized. Please start again.")
        return redirect('accounts:forgot_password')
        
    if request.method == 'POST':
        pass1 = request.POST.get('password')
        pass2 = request.POST.get('confirm_password')
        
        if pass1 != pass2:
            messages.error(request, "Passwords do not match.")
        elif len(pass1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
        else:
            user = get_object_or_404(CustomUser, email=email)
            user.set_password(pass1)
            user.save()
            
            # Clear session
            del request.session['reset_email']
            del request.session['otp_verified']
            
            messages.success(request, "Your password has been reset successfully. Please login with your new password.")
            return redirect('accounts:login')
            
    return render(request, 'accounts/reset_password.html')


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
