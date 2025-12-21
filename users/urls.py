from django.urls import path
from . import views

# Admin用のURL
urlpatterns = [
    path('', views.user_list, name='user_list'),
    path('create/', views.user_create, name='user_create'),
    path('<int:user_id>/', views.user_detail, name='user_detail'),
    path('<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('<int:user_id>/delete/', views.user_delete, name='user_delete'),
]

# 一般ユーザー用のURL（別途user_urlpatternsとしてインポート可能）
user_urlpatterns = [
    path('', views.general_user_list, name='general_user_list'),
    path('create/', views.general_user_create, name='general_user_create'),
    path('<int:user_id>/', views.general_user_detail, name='general_user_detail'),
    path('<int:user_id>/edit/', views.general_user_edit, name='general_user_edit'),
    path('<int:user_id>/delete/', views.general_user_delete, name='general_user_delete'),
]
