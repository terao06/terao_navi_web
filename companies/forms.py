from django import forms
from .models import Company


class CompanyForm(forms.ModelForm):
    """会社フォーム"""
    class Meta:
        model = Company
        fields = ['name', 'address', 'tel', 'home_page']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会社名'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '住所'}),
            'tel': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '電話番号'}),
            'home_page': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '会社ホームページ'}),
        }
        labels = {
            'name': '会社名',
            'address': '住所',
            'tel': '電話番号',
            'home_page': '会社ホームページ'
        }
