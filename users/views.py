from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from companies.models import Company
from .models import User, Role
from .forms import UserForm


def is_superuser(user):
    """スーパーユーザーかどうかをチェック"""
    return user.is_authenticated and user.is_superuser


def require_user_authentication(view_func):
    """一般ユーザー認証デコレータ"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_user_authenticated'):
            messages.error(request, 'ログインが必要です。')
            return redirect('/user/login/')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_current_user(request):
    """セッションから現在のユーザーを取得"""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            return User.objects.select_related('company', 'role').get(user_id=user_id)
        except User.DoesNotExist:
            return None
    return None


# ========== Admin用User管理Views ==========

@user_passes_test(is_superuser, login_url='/login/')
def user_list(request):
    """ユーザー一覧"""
    query = request.GET.get('q', '')
    company_filter = request.GET.get('company', '')
    
    users = User.objects.select_related('company').all()
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    if company_filter:
        users = users.filter(company_id=company_filter)
    
    companies = Company.objects.all()
    
    context = {
        'users': users.order_by('-created_at'),
        'companies': companies,
        'query': query,
        'company_filter': company_filter,
    }
    return render(request, 'admin/users/user_list.html', context)


@user_passes_test(is_superuser, login_url='/login/')
def user_create(request):
    """ユーザー作成"""
    if request.method == 'POST':
        form = UserForm(request.POST, for_admin=True)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'ユーザー「{user.username}」を作成しました。')
            return redirect('user_list')
    else:
        form = UserForm(for_admin=True)
    
    return render(request, 'admin/users/user_form.html', {
        'form': form, 
        'title': 'ユーザー作成',
        'user': None,  # 新規作成時はNoneを明示
    })


@user_passes_test(is_superuser, login_url='/login/')
def user_edit(request, user_id):
    """ユーザー編集"""
    user = get_object_or_404(User, user_id=user_id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user, for_admin=True)
        if form.is_valid():
            user = form.save(commit=False)
            
            # 編集時、パスワードが入力されていない場合は既存のパスワードを保持
            if not form.cleaned_data.get('password'):
                user.password = User.objects.get(user_id=user_id).password
            
            user.save()
            messages.success(request, f'ユーザー「{user.username}」を更新しました。')
            return redirect('user_list')
    else:
        form = UserForm(instance=user, for_admin=True)
    
    return render(request, 'admin/users/user_form.html', {'form': form, 'title': 'ユーザー編集', 'user': user})


@user_passes_test(is_superuser, login_url='/login/')
def user_delete(request, user_id):
    """ユーザー削除"""
    user = get_object_or_404(User, user_id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'ユーザー「{username}」を削除しました。')
        return redirect('user_list')
    
    return render(request, 'admin/users/user_confirm_delete.html', {'user': user})


@user_passes_test(is_superuser, login_url='/login/')
def user_detail(request, user_id):
    """ユーザー詳細"""
    user = get_object_or_404(User.objects.select_related('company'), user_id=user_id)
    return render(request, 'admin/users/user_detail.html', {'user': user})


# ========== 一般ユーザー用User管理Views ==========

@require_user_authentication
def general_user_list(request):
    """ユーザー一覧（同一company_id内のみ、自分自身を除く）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    query = request.GET.get('q', '')
    # 自分自身を除外
    users = User.objects.filter(company_id=current_user.company_id).exclude(user_id=current_user.user_id).select_related('company', 'role')
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    context = {
        'users': users.order_by('-created_at'),
        'query': query,
        'current_user': current_user,
        'can_create': current_user.role_id in [Role.FULL_ACCESS, Role.LIMITED_ACCESS],
    }
    return render(request, 'user/users/user_list.html', context)


@require_user_authentication
def general_user_create(request):
    """ユーザー作成（role_id 1,2のみ）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    if current_user.role_id == Role.READ_ONLY:
        messages.error(request, 'ユーザーを作成する権限がありません。')
        return redirect('general_user_list')
    
    if request.method == 'POST':
        form = UserForm(request.POST, current_user=current_user)
        if form.is_valid():
            user = form.save(commit=False)
            user.company = current_user.company
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f'ユーザー「{user.username}」を作成しました。')
            return redirect('general_user_list')
    else:
        form = UserForm(current_user=current_user)
    
    return render(request, 'user/users/user_form.html', {
        'form': form,
        'title': 'ユーザー作成',
        'current_user': current_user,
        'user': None,  # 新規作成時はNoneを明示
    })


@require_user_authentication
def general_user_edit(request, user_id):
    """ユーザー編集（role_id 1,2のみ、同一company_id内のみ）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    if current_user.role_id == Role.READ_ONLY:
        messages.error(request, 'ユーザーを編集する権限がありません。')
        return redirect('general_user_list')
    
    user = get_object_or_404(User, user_id=user_id, company_id=current_user.company_id)
    
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user, current_user=current_user)
        if form.is_valid():
            user = form.save(commit=False)
            # 会社フィールドが非表示なので、明示的に設定
            user.company = current_user.company
            
            # 編集時、パスワードが入力されていない場合は既存のパスワードを保持
            if not form.cleaned_data.get('password'):
                user.password = User.objects.get(user_id=user_id).password
            
            user.save()
            messages.success(request, f'ユーザー「{user.username}」を更新しました。')
            return redirect('general_user_list')
    else:
        form = UserForm(instance=user, current_user=current_user)
    
    return render(request, 'user/users/user_form.html', {
        'form': form,
        'title': 'ユーザー編集',
        'user': user,
        'current_user': current_user,
    })


@require_user_authentication
def general_user_delete(request, user_id):
    """ユーザー削除（role_id 1,2のみ、同一company_id内のみ）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    if current_user.role_id == Role.READ_ONLY:
        messages.error(request, 'ユーザーを削除する権限がありません。')
        return redirect('general_user_list')
    
    user = get_object_or_404(User, user_id=user_id, company_id=current_user.company_id)
    
    if user.user_id == current_user.user_id:
        messages.error(request, '自分自身を削除することはできません。')
        return redirect('general_user_list')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'ユーザー「{username}」を削除しました。')
        return redirect('general_user_list')
    
    return render(request, 'user/users/user_confirm_delete.html', {
        'user': user,
        'current_user': current_user,
    })


@require_user_authentication
def general_user_detail(request, user_id):
    """ユーザー詳細（同一company_id内のみ）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    user = get_object_or_404(User.objects.select_related('company', 'role'), 
                            user_id=user_id, 
                            company_id=current_user.company_id)
    
    return render(request, 'user/users/user_detail.html', {
        'user': user,
        'current_user': current_user,
        'can_edit': current_user.role_id in [Role.FULL_ACCESS, Role.LIMITED_ACCESS],
    })
