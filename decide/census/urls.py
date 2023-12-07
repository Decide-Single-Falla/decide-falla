from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('list/<int:voting_id>/', views.CensusListView.as_view(), name='census_list'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
]
