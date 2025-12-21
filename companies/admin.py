from django.contrib import admin
from django.utils.html import format_html
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """会社管理画面"""
    list_display = ('company_id', 'name', 'tel', 'address', 'is_deleted_display', 'created_at', 'updated_at')
    list_display_links = ('company_id', 'name')
    search_fields = ('name', 'tel', 'address')
    list_filter = ('is_deleted', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    actions = ['restore_items']

    fieldsets = (
        ('基本情報', {
            'fields': ('name', 'tel', 'address')
        }),
        ('削除情報', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
        ('システム情報', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """削除済みを含むすべてのレコードを表示"""
        return Company.all_objects.all()

    def is_deleted_display(self, obj):
        """削除状態を色付きで表示"""
        if obj.is_deleted:
            return format_html('<span style="color: red;">削除済み</span>')
        return format_html('<span style="color: green;">有効</span>')
    is_deleted_display.short_description = '状態'

    def restore_items(self, request, queryset):
        """選択したアイテムを復元"""
        count = 0
        for item in queryset:
            if item.is_deleted:
                item.restore()
                count += 1
        self.message_user(request, f'{count}件の会社を復元しました。')
    restore_items.short_description = '選択した会社を復元'

