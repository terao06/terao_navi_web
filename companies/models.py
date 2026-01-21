from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """論理削除用マネージャー"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        """削除済みを含むすべてのレコードを取得"""
        return super().get_queryset()
    
    def deleted_only(self):
        """削除済みのレコードのみを取得"""
        return super().get_queryset().filter(is_deleted=True)


class Company(models.Model):
    """会社モデル"""
    company_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='会社名')
    address = models.CharField(max_length=255, verbose_name='住所')
    tel = models.CharField(max_length=255, verbose_name='電話番号')
    home_page = models.CharField(max_length=255, verbose_name='会社ホームページ')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='削除日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'companies'
        verbose_name = '会社'
        verbose_name_plural = '会社'

    def __str__(self):
        return self.name
    
    def delete(self, using=None, keep_parents=False):
        """論理削除（関連するユーザー、アプリケーション、マニュアルも削除）"""
        # 関連するアプリケーションを削除（これによりマニュアルも削除される）
        for application in self.applications.filter(is_deleted=False):
            application.delete()
        
        # 関連するユーザーを論理削除
        for user in self.users.filter(is_deleted=False):
            user.delete()
        
        # 会社自体を論理削除
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
