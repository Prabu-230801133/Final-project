from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('election/<int:election_id>/', views.election_detail, name='election_detail'),
    path('election/<int:election_id>/vote/', views.cast_vote, name='cast_vote'),
    path('election/<int:election_id>/verify-otp/', views.verify_vote_otp, name='verify_vote_otp'),
    path('election/<int:election_id>/feedback/', views.vote_feedback, name='vote_feedback'),
    path('election/<int:election_id>/success/', views.vote_success, name='vote_success'),
    path('results/<int:election_id>/', views.election_results, name='election_results'),
]
