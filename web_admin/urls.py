from django.urls import path
from . import views

app_name = 'web_admin'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Election management
    path('elections/', views.elections_list, name='elections_list'),
    path('elections/create/', views.election_create, name='election_create'),
    path('elections/<int:election_id>/', views.election_detail_admin, name='election_detail'),
    path('elections/<int:election_id>/delete/', views.election_delete, name='election_delete'),
    path('elections/<int:election_id>/publish/', views.election_publish, name='election_publish'),

    # Position management
    path('elections/<int:election_id>/positions/add/', views.position_add, name='position_add'),
    path('positions/<int:position_id>/delete/', views.position_delete, name='position_delete'),

    # Candidate management
    path('positions/<int:position_id>/candidates/add/', views.candidate_add, name='candidate_add'),
    path('candidates/<int:candidate_id>/delete/', views.candidate_delete, name='candidate_delete'),

    # Voter assignment
    path('elections/<int:election_id>/voters/add/', views.assign_voter, name='assign_voter'),
    path('elections/<int:election_id>/voters/<int:user_id>/remove/', views.remove_voter, name='remove_voter'),

    # Results
    path('elections/<int:election_id>/results/', views.live_results, name='live_results'),
    path('elections/<int:election_id>/results/api/', views.live_results_api, name='live_results_api'),

    # Students
    path('students/', views.students_list, name='students_list'),
]
