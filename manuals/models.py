from django.db import models
from companies.models import Company
from applications.models import Application


class SoftDeleteManager(models.Manager):
    """論理削除用のカスタムマネージャー"""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class Manual(models.Model):
    """マニュアルモデル"""
    manual_id = models.AutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='manuals')
    manual_name = models.CharField(max_length=200, verbose_name='マニュアル名')
    description = models.TextField(blank=True, null=True, verbose_name='説明')
    file_path = models.CharField(max_length=500, verbose_name='ファイルパス')  # S3内のパス: manuals/application_id/manual_id.pdf
    file_size = models.BigIntegerField(verbose_name='ファイルサイズ(bytes)', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='削除日時')

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'manuals'
        indexes = [
            models.Index(fields=['application']),
            models.Index(fields=['is_deleted']),
        ]
        verbose_name = 'マニュアル'
        verbose_name_plural = 'マニュアル'
    
    @property
    def company(self):
        """アプリケーションから会社を取得"""
        return self.application.company
    
    @property
    def company_id(self):
        """アプリケーションから会社IDを取得"""
        return self.application.company_id

    def __str__(self):
        return self.manual_name

    def delete(self, using=None, keep_parents=False):
        """論理削除"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
