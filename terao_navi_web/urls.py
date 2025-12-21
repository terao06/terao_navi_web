"""
URL configuration for terao_navi_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from users.urls import user_urlpatterns

urlpatterns = [
    path('', views.home, name='home'),
    # Admin用ログイン
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    # 一般ユーザー用
    path('user/login/', views.user_login, name='user_login'),
    path('user/logout/', views.user_logout, name='user_logout'),
    path('user/home/', views.user_home, name='user_home'),
    path('user/users/', include(user_urlpatterns)),  # 一般ユーザー用のユーザー管理
    path('user/applications/', include('applications.urls')),  # アプリケーション管理
    path('user/manuals/', include('manuals.urls')),  # マニュアル管理
    # Django Admin（カスタム管理画面へリダイレクト）
    path('admin/', views.admin_redirect, name='admin_redirect'),
    # カスタム管理画面（スーパーユーザー用）
    path('companies/', include('companies.urls')),
    path('users/', include('users.urls')),
]
