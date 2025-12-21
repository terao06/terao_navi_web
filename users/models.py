from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from companies.models import Company, SoftDeleteManager


class Role(models.Model):
    """ロールモデル"""
    FULL_ACCESS = 1
    LIMITED_ACCESS = 2
    READ_ONLY = 3
    
    ROLE_CHOICES = [
        (FULL_ACCESS, '全権限付与'),
        (LIMITED_ACCESS, '制限された範囲内で登録更新が可能'),
        (READ_ONLY, '閲覧権限のみ'),
    ]
    
    role_id = models.IntegerField(primary_key=True, choices=ROLE_CHOICES)
    name = models.CharField(max_length=50, verbose_name='ロール名')
    description = models.TextField(blank=True, null=True, verbose_name='説明')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    
    class Meta:
        db_table = 'roles'
        verbose_name = 'ロール'
        verbose_name_plural = 'ロール'
    
    def __str__(self):
        return self.name


class User(models.Model):
    """ユーザーモデル"""
    user_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='会社',
        db_column='company_id'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='users',
        verbose_name='ロール',
        db_column='role_id',
        default=Role.READ_ONLY
    )
    username = models.CharField(max_length=150, unique=True, verbose_name='ユーザー名')
    email = models.EmailField(max_length=255, verbose_name='メールアドレス')
    password = models.CharField(max_length=255, verbose_name='パスワード')
    first_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='名')
    last_name = models.CharField(max_length=150, blank=True, null=True, verbose_name='姓')
    is_active = models.BooleanField(default=True, verbose_name='有効')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='削除日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"{self.username} ({self.company.name})"

    def set_password(self, raw_password):
        """パスワードをハッシュ化して保存"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """パスワードを検証"""
        return check_password(raw_password, self.password)
    
    def has_full_access(self):
        """全権限を持っているか"""
        return self.role_id == Role.FULL_ACCESS
    
    def has_write_access(self):
        """書き込み権限を持っているか（全権限または制限付き権限）"""
        return self.role_id in [Role.FULL_ACCESS, Role.LIMITED_ACCESS]
    
    def has_read_only(self):
        """閲覧権限のみか"""
        return self.role_id == Role.READ_ONLY

    @property
    def full_name(self):
        """フルネームを取得"""
        if self.last_name and self.first_name:
            return f"{self.last_name} {self.first_name}"
        return self.username
    
    def delete(self, using=None, keep_parents=False):
        """論理削除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def hard_delete(self):
        """物理削除"""
        super().delete()
    
    def restore(self):
        """削除を取り消す"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()
