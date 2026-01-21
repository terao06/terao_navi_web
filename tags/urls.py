from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_script_tag, name='generate_script_tag'),
]
