from django import forms
from .models import Application


class ApplicationForm(forms.ModelForm):
    """アプリケーションフォーム"""
    
    class Meta:
        model = Application
        fields = ['application_name', 'description']
        widgets = {
            'application_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'アプリケーション名'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '説明', 'rows': 4}),
        }
        labels = {
            'application_name': 'アプリケーション名',
            'description': '説明',
        }
