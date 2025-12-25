from django import forms
from companies.models import Company
from .models import User, Role


class UserForm(forms.ModelForm):
    """ユーザーフォーム（Admin用と一般ユーザー用で共通）"""
    password_confirm = forms.CharField(
        label='パスワード（確認）',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'パスワード（確認）'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'company', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ユーザー名'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'メールアドレス'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'パスワード'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '名'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '姓'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, current_user=None, for_admin=False, **kwargs):
        """
        Args:
            current_user: 一般ユーザーの場合、現在のユーザー
            for_admin: True=Admin画面用、False=一般ユーザー用
        """
        super().__init__(*args, **kwargs)
        
        if for_admin:
            # Admin画面: 全権限付与のみ
            self.fields['role'].queryset = Role.objects.filter(role_id=Role.FULL_ACCESS)
            self.fields['role'].initial = Role.FULL_ACCESS
            self.fields['role'].required = True
        elif current_user:
            # 一般ユーザー用: ロールによって選択可能なロールを制限
            # current_user.role_idでアクセス（ForeignKeyのdb_columnがrole_idのため）
            user_role_id = current_user.role_id if hasattr(current_user, 'role_id') else current_user.role.role_id
            
            if user_role_id == Role.FULL_ACCESS:
                # role_id=1: 2と3のみ登録可能
                self.fields['role'].queryset = Role.objects.filter(role_id__in=[Role.LIMITED_ACCESS, Role.READ_ONLY])
                self.fields['role'].initial = Role.LIMITED_ACCESS
            elif user_role_id == Role.LIMITED_ACCESS:
                # role_id=2: 3のみ登録可能
                self.fields['role'].queryset = Role.objects.filter(role_id=Role.READ_ONLY)
                self.fields['role'].initial = Role.READ_ONLY
            else:
                # role_id=3: 登録不可
                self.fields['role'].queryset = Role.objects.none()
            
            # 会社フィールドを非表示（自動的に同じ会社に設定）
            self.fields['company'].widget = forms.HiddenInput()
            self.fields['company'].required = False
        
        # 編集時、パスワードフィールドを非表示にする
        if self.instance.pk:
            self.fields['password'].widget = forms.HiddenInput()
            self.fields['password'].required = False
            self.fields['password_confirm'].widget = forms.HiddenInput()
            self.fields['password_confirm'].required = False

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('パスワードが一致しません')

        return cleaned_data
    
    def clean_username(self):
        """ユーザー名の重複チェック"""
        username = self.cleaned_data.get('username')
        
        # 編集時は自分自身を除外
        if self.instance.pk:
            if User.all_objects.filter(username=username).exclude(user_id=self.instance.pk).exists():
                raise forms.ValidationError('このユーザー名は既に使用されています。')
        else:
            # 新規作成時（論理削除されたものも含めてチェック）
            if User.all_objects.filter(username=username).exists():
                raise forms.ValidationError('このユーザー名は既に使用されています。')
        
        return username
    
    def clean_email(self):
        """メールアドレスの重複チェック"""
        email = self.cleaned_data.get('email')
        
        # 編集時は自分自身を除外
        if self.instance.pk:
            if User.all_objects.filter(email=email).exclude(user_id=self.instance.pk).exists():
                raise forms.ValidationError('このメールアドレスは既に使用されています。')
        else:
            # 新規作成時（論理削除されたものも含めてチェック）
            if User.all_objects.filter(email=email).exists():
                raise forms.ValidationError('このメールアドレスは既に使用されています。')
        
        return email
