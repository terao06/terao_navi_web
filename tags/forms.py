from django import forms


class ScriptTagForm(forms.Form):
    """スクリプトタグ生成フォーム"""
    chat_title = forms.CharField(
        max_length=100,
        initial='AIチャットへ質問する',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'チャットタイトル'}),
        label='チャットタイトル'
    )
    chat_color = forms.CharField(
        max_length=7,
        initial='#667eea',
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        label='チャットカラー'
    )
