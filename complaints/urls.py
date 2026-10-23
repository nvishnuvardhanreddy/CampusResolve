from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/counts/', views.dashboard_counts, name='dashboard_counts'),
    path('complaints/new/', views.create_complaint, name='create_complaint'),
    path('complaints/<int:pk>/', views.complaint_detail, name='complaint_detail'),
]
