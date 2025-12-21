from django.db import models
from companies.models import Company, SoftDeleteManager


class Application(models.Model):
    """アプリケーションモデル"""
    application_id = models.AutoField(primary_key=True)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='会社',
        db_column='company_id'
    )
    application_name = models.CharField(max_length=255, verbose_name='アプリケーション名')
    description = models.TextField(blank=True, null=True, verbose_name='説明')
    is_deleted = models.BooleanField(default=False, verbose_name='削除フラグ')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='削除日時')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        db_table = 'applications'
        verbose_name = 'アプリケーション'
        verbose_name_plural = 'アプリケーション'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['application_name']),
        ]

    def __str__(self):
        return f"{self.application_name} ({self.company.name})"

    def delete(self, using=None, keep_parents=False):
        """論理削除（紐づくマニュアルも削除）"""
        from django.utils import timezone
        
        # 紐づくマニュアルも論理削除
        for manual in self.manuals.filter(is_deleted=False):
            manual.delete()
        
        # アプリケーション自体を論理削除
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
