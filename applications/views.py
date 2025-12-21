from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from .models import Application
from .forms import ApplicationForm
from companies.models import Company


def require_user_authentication(view_func):
    """一般ユーザー認証デコレーター"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_user_authenticated'):
            messages.error(request, 'ログインが必要です。')
            return redirect('/user/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_current_user(request):
    """セッションから現在のユーザーを取得"""
    from users.models import User
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return User.objects.get(user_id=user_id, is_active=True)
        except User.DoesNotExist:
            return None
    return None


@require_user_authentication
def application_list(request):
    """アプリケーション一覧（同一company_id内のみ）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    query = request.GET.get('q', '')
    applications = Application.objects.filter(company_id=current_user.company_id).select_related('company')
    
    if query:
        applications = applications.filter(
            Q(application_name__icontains=query) |
            Q(description__icontains=query)
        )
    
    context = {
        'applications': applications.order_by('-created_at'),
        'query': query,
        'current_user': current_user,
    }
    return render(request, 'user/applications/application_list.html', context)


@require_user_authentication
def application_create(request):
    """アプリケーション作成"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    # 書き込み権限チェック（READ_ONLYは不可）
    if current_user.role_id == 3:  # READ_ONLY
        messages.error(request, 'アプリケーションを作成する権限がありません。')
        return redirect('application_list')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.company = current_user.company
            application.save()
            messages.success(request, f'アプリケーション「{application.application_name}」を作成しました。')
            return redirect('application_list')
    else:
        form = ApplicationForm()
    
    return render(request, 'user/applications/application_form.html', {
        'form': form,
        'title': 'アプリケーション作成',
        'current_user': current_user,
        'application': None,
    })


@require_user_authentication
def application_edit(request, application_id):
    """アプリケーション編集"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    # 書き込み権限チェック（READ_ONLYは不可）
    if current_user.role_id == 3:  # READ_ONLY
        messages.error(request, 'アプリケーションを編集する権限がありません。')
        return redirect('application_list')
    
    application = get_object_or_404(Application, application_id=application_id, company_id=current_user.company_id)
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save(commit=False)
            application.company = current_user.company
            application.save()
            messages.success(request, f'アプリケーション「{application.application_name}」を更新しました。')
            return redirect('application_list')
    else:
        form = ApplicationForm(instance=application)
    
    return render(request, 'user/applications/application_form.html', {
        'form': form,
        'title': 'アプリケーション編集',
        'application': application,
        'current_user': current_user,
    })


@require_user_authentication
def application_delete(request, application_id):
    """アプリケーション削除"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    # 書き込み権限チェック（READ_ONLYは不可）
    if current_user.role_id == 3:  # READ_ONLY
        messages.error(request, 'アプリケーションを削除する権限がありません。')
        return redirect('application_list')
    
    application = get_object_or_404(Application, application_id=application_id, company_id=current_user.company_id)
    
    if request.method == 'POST':
        application_name = application.application_name
        application.delete()
        messages.success(request, f'アプリケーション「{application_name}」を削除しました。')
        return redirect('application_list')
    
    return render(request, 'user/applications/application_delete.html', {
        'application': application,
        'current_user': current_user,
    })


@require_user_authentication
def application_detail(request, application_id):
    """アプリケーション詳細"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    application = get_object_or_404(Application, application_id=application_id, company_id=current_user.company_id)
    
    return render(request, 'user/applications/application_detail.html', {
        'application': application,
        'current_user': current_user,
    })
