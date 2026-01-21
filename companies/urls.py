from django.urls import path
from . import views

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('create/', views.company_create, name='company_create'),
    path('<int:company_id>/', views.company_detail, name='company_detail'),
    path('<int:company_id>/edit/', views.company_edit, name='company_edit'),
    path('<int:company_id>/delete/', views.company_delete, name='company_delete'),
]
