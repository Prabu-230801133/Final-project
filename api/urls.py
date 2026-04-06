from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('elections/', views.elections_list, name='elections_list'),
    path('candidates/<int:election_id>/', views.candidates_list, name='candidates_list'),
    path('results/<int:election_id>/', views.election_results, name='election_results'),
    path('my-votes/', views.my_votes, name='my_votes'),
]
