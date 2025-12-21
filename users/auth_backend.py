from django.contrib.auth.backends import BaseBackend
from users.models import User


class UserAuthBackend(BaseBackend):
    """usersテーブルの一般ユーザー用認証バックエンド"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """ユーザー認証（メールアドレスまたはユーザー名で認証）"""
        try:
            # メールアドレスで検索
            user = User.objects.get(email=username, is_active=True)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # メールアドレスで見つからない場合はユーザー名で検索
            try:
                user = User.objects.get(username=username, is_active=True)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        return None
    
    def get_user(self, user_id):
        """ユーザーIDからユーザーを取得"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
