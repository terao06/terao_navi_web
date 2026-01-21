from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        """アプリケーション起動時に実行"""
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        
        @receiver(post_migrate, sender=self)
        def create_default_roles(sender, **kwargs):
            """デフォルトのロールを作成"""
            from users.models import Role
            
            roles = [
                {'role_id': 1, 'name': '全権限付与', 'description': 'すべての機能にアクセスできる権限'},
                {'role_id': 2, 'name': '閲覧・編集権限', 'description': 'データの閲覧と編集ができる権限'},
                {'role_id': 3, 'name': '閲覧権限', 'description': 'データの閲覧のみできる権限'},
            ]
            
            for role_data in roles:
                Role.objects.get_or_create(
                    role_id=role_data['role_id'],
                    defaults={
                        'name': role_data['name'],
                        'description': role_data['description']
                    }
                )
