from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect/', views.redirect_view, name='redirect'),
    # Password Reset flow
    path('password-reset/', views.forgot_password, name='forgot_password'),
    path('password-reset/verify/', views.verify_password_otp, name='verify_password_otp'),
    path('password-reset/confirm/', views.reset_password, name='reset_password'),
]
