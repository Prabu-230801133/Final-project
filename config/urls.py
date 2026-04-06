from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from voting import views as voting_views

urlpatterns = [
    # Django Admin
    path('django-admin/', admin.site.urls),

    # Social Auth (Google OAuth)
    path('social-auth/', include('social_django.urls', namespace='social')),

    # Accounts (login, logout, register)
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Voting (student dashboard, vote casting)
    path('voting/', include('voting.urls', namespace='voting')),

    # Web Admin Dashboard
    path('admin-dashboard/', include('web_admin.urls', namespace='web_admin')),

    # REST API
    path('api/', include('api.urls', namespace='api')),

    # AI Chatbot
    path('chat/', include('chat.urls', namespace='chat')),

    # Public landing page
    path('', voting_views.home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
