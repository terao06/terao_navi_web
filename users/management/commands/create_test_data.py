from django.core.management.base import BaseCommand
from users.models import Company, User


class Command(BaseCommand):
    help = 'テストデータを作成します'

    def handle(self, *args, **kwargs):
        # 会社を作成
        company1, _ = Company.objects.get_or_create(
            name='株式会社テラオ',
            defaults={
                'address': '東京都渋谷区xxx-xxx',
                'tel': '03-1234-5678'
            }
        )
        self.stdout.write(self.style.SUCCESS(f'会社を作成: {company1.name}'))

        company2, _ = Company.objects.get_or_create(
            name='サンプル株式会社',
            defaults={
                'address': '大阪府大阪市xxx-xxx',
                'tel': '06-9876-5432'
            }
        )
        self.stdout.write(self.style.SUCCESS(f'会社を作成: {company2.name}'))

        # ユーザーを作成
        users_data = [
            {
                'username': 'yamada',
                'email': 'yamada@terao.com',
                'first_name': '太郎',
                'last_name': '山田',
                'company': company1,
                'is_staff': True,
            },
            {
                'username': 'tanaka',
                'email': 'tanaka@terao.com',
                'first_name': '花子',
                'last_name': '田中',
                'company': company1,
            },
            {
                'username': 'suzuki',
                'email': 'suzuki@sample.com',
                'first_name': '次郎',
                'last_name': '鈴木',
                'company': company2,
            },
        ]

        for user_data in users_data:
            username = user_data['username']
            if not User.objects.filter(username=username).exists():
                user = User(**user_data)
                user.set_password('password123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'ユーザーを作成: {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'ユーザーは既に存在します: {username}'))

        self.stdout.write(self.style.SUCCESS('テストデータの作成が完了しました！'))
