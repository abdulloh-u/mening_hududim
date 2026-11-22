from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('yuborish/', views.report_create_view, name='create'),
    path('murojaat/<str:tracking_code>/muvaffaqiyat/', views.report_success_view, name='success'),
    path('report/<str:tracking_code>/', views.report_detail_view, name='detail'),
    path('murojaatlar/', views.report_list_view, name='list'),
    path('xarita/', views.report_map_view, name='map'),
    path('kuzatish/', views.report_track_view, name='track'),
    path('biz-haqimizda/', views.about_view, name='about'),

    # JSON APIs for interactive map
    path('api/reports-geojson/', views.reports_api_geojson, name='api_geojson'),
    path('api/regions-geojson/', views.regions_geojson_view, name='api_regions_geojson'),
]
