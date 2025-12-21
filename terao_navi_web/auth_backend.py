from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """メールアドレスまたはユーザー名でログインできる認証バックエンド"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """メールアドレスまたはユーザー名で認証"""
        try:
            # まずメールアドレスで検索
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # メールアドレスで見つからない場合はユーザー名で検索
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        # パスワードチェック
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
