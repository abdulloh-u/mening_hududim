from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home_view, name='index'),
    path('murojaatlar/', views.dashboard_reports_list_view, name='report_list'),
    path('murojaat/<str:tracking_code>/', views.dashboard_report_detail_view, name='report_detail'),
    path('xodimlar/', views.dashboard_staff_list_view, name='staff_list'),
    path('xodimlar/yangi/', views.dashboard_staff_create_view, name='staff_create'),
    path('xodimlar/viloyat-adminlari/', views.dashboard_region_admins_view, name='region_admins'),
    path('xodimlar/<int:user_id>/holat/', views.dashboard_staff_toggle_view, name='staff_toggle'),
    path('sozlamalar/', views.admin_settings_view, name='settings'),
    path('statistika/', views.dashboard_statistics_view, name='statistics'),
    path('eksport/csv/', views.export_reports_csv, name='export_csv'),
]
