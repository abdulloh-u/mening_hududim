from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('api/districts/<int:region_id>/', views.get_districts_by_region, name='districts_by_region'),
]
