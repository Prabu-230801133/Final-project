from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('api/', views.chatbot_api, name='chatbot_api'),
]
