from django.urls import path
from . import views

urlpatterns = [
    path('', views.application_list, name='application_list'),
    path('create/', views.application_create, name='application_create'),
    path('<int:application_id>/', views.application_detail, name='application_detail'),
    path('<int:application_id>/edit/', views.application_edit, name='application_edit'),
    path('<int:application_id>/delete/', views.application_delete, name='application_delete'),
]
