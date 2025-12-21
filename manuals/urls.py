from django.urls import path
from . import views

urlpatterns = [
    path('', views.manual_list, name='manual_list'),
    path('create/', views.manual_create, name='manual_create'),
    path('<int:manual_id>/', views.manual_detail, name='manual_detail'),
    path('<int:manual_id>/edit/', views.manual_edit, name='manual_edit'),
    path('<int:manual_id>/delete/', views.manual_delete, name='manual_delete'),
    path('<int:manual_id>/preview/', views.manual_preview, name='manual_preview'),
]
