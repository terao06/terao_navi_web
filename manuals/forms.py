from django import forms
from .models import Manual
from applications.models import Application


class ManualForm(forms.ModelForm):
    """マニュアルフォーム"""
    pdf_file = forms.FileField(
        label='PDFファイル',
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        help_text='PDFファイルのみアップロード可能です'
    )
    
    class Meta:
        model = Manual
        fields = ['application', 'manual_name', 'description']
        widgets = {
            'application': forms.Select(attrs={'class': 'form-control'}),
            'manual_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'マニュアル名'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': '説明', 'rows': 4}),
        }
        labels = {
            'application': 'アプリケーション',
            'manual_name': 'マニュアル名',
            'description': '説明',
        }
    
    def __init__(self, *args, current_user=None, **kwargs):
        """
        Args:
            current_user: 現在のユーザー（会社でアプリケーションをフィルタリング）
        """
        super().__init__(*args, **kwargs)
        
        if current_user:
            # 同じ会社のアプリケーションのみ表示
            self.fields['application'].queryset = Application.objects.filter(
                company_id=current_user.company_id
            )
        
        # 編集時はファイルを必須にしない
        if self.instance and self.instance.pk:
            self.fields['pdf_file'].required = False
            self.fields['pdf_file'].help_text = 'ファイルを変更する場合のみ選択してください'
    
    def clean_pdf_file(self):
        """PDFファイルのバリデーション"""
        pdf_file = self.cleaned_data.get('pdf_file')
        
        # 新規作成時はファイル必須
        if not self.instance.pk and not pdf_file:
            raise forms.ValidationError('PDFファイルを選択してください。')
        
        if pdf_file:
            # ファイルサイズチェック (50MB以下)
            if pdf_file.size > 50 * 1024 * 1024:
                raise forms.ValidationError('ファイルサイズは50MB以下にしてください。')
            
            # ファイル拡張子チェック
            if not pdf_file.name.lower().endswith('.pdf'):
                raise forms.ValidationError('PDFファイルのみアップロード可能です。')
        
        return pdf_file
