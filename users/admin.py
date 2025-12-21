from django.contrib import admin
from django.utils.html import format_html
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """ロール管理画面"""
    list_display = ('role_id', 'name', 'description', 'created_at', 'updated_at')
    list_display_links = ('role_id', 'name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('role_id',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """ユーザー管理画面"""
    list_display = ('user_id', 'username', 'email', 'full_name', 'company', 'role', 'is_active', 'is_deleted_display', 'created_at')
    list_display_links = ('user_id', 'username')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'company__name')
    list_filter = ('is_active', 'role', 'is_deleted', 'company', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    actions = ['restore_items']
    
    fieldsets = (
        ('基本情報', {
            'fields': ('username', 'email', 'password')
        }),
        ('個人情報', {
            'fields': ('last_name', 'first_name')
        }),
        ('会社情報', {
            'fields': ('company',)
        }),
        ('権限', {
            'fields': ('role', 'is_active')
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
        return User.all_objects.select_related('company').all()

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
        self.message_user(request, f'{count}件のユーザーを復元しました。')
    restore_items.short_description = '選択したユーザーを復元'

    def save_model(self, request, obj, form, change):
        """保存時にパスワードをハッシュ化"""
        if 'password' in form.changed_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)


