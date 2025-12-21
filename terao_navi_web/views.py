from django.shortcuts import render, redirect
from django.contrib.auth import logout, authenticate, login
from django.contrib import messages
from users.auth_backend import UserAuthBackend


# ========== 共通 ==========

def home(request):
    """ホームページ - デフォルトでユーザーログイン画面へ"""
    # スーパーユーザーでログイン済みの場合は管理画面へ
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/companies/')
    # 一般ユーザーでログイン済みの場合はユーザー管理画面へ
    if request.session.get('is_user_authenticated'):
        return redirect('/user/users/')
    # 未ログインの場合はユーザーログイン画面へ（お客様向け）
    return redirect('/user/login/')


def admin_redirect(request):
    """Django管理サイトからカスタム管理画面へリダイレクト"""
    # スーパーユーザーでログイン済みの場合は会社一覧へ
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('/companies/')
    # 未ログインの場合は管理者ログイン画面へ
    return redirect('/login/')


# ========== Admin用（スーパーユーザー） ==========

def custom_login(request):
    """管理者ログイン（メールアドレスまたはユーザー名で認証）"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # まずメールアドレスで試す
        user = authenticate(request, username=username, password=password)
        
        # メールアドレスで失敗した場合、標準のusernameで試す
        if user is None:
            # Django標準のauthenticateは既にusernameで試している
            pass
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                next_url = request.POST.get('next') or request.GET.get('next') or '/companies/'
                return redirect(next_url)
            else:
                messages.error(request, 'スーパーユーザーのみアクセスできます。')
        else:
            messages.error(request, 'メールアドレス/ユーザー名またはパスワードが正しくありません。')
    
    next_url = request.GET.get('next', '/companies/')
    return render(request, 'admin/login.html', {'next': next_url})


def custom_logout(request):
    """管理者ログアウト"""
    logout(request)
    messages.success(request, 'ログアウトしました。')
    return render(request, 'admin/logout.html')


# ========== 一般ユーザー用 ==========

def user_login(request):
    """一般ユーザーログイン（メールアドレスまたはユーザー名で認証）"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # カスタム認証バックエンドで認証
        auth_backend = UserAuthBackend()
        user = auth_backend.authenticate(request, username=username, password=password)
        
        if user is not None:
            # セッションにユーザー情報を保存
            request.session['user_id'] = user.user_id
            request.session['user_username'] = user.username
            request.session['user_company_name'] = user.company.name
            request.session['is_user_authenticated'] = True
            
            next_url = request.POST.get('next') or request.GET.get('next') or '/user/users/'
            return redirect(next_url)
        else:
            messages.error(request, 'メールアドレス/ユーザー名またはパスワードが正しくありません。')
    
    next_url = request.GET.get('next', '/user/users/')
    return render(request, 'user/login.html', {'next': next_url})


def user_logout(request):
    """一般ユーザーログアウト"""
    # セッションからユーザー情報を削除
    request.session.flush()
    messages.success(request, 'ログアウトしました。')
    return render(request, 'user/logout.html')


def user_home(request):
    """一般ユーザーホーム - ユーザー管理画面へリダイレクト"""
    # セッション認証チェック
    if not request.session.get('is_user_authenticated'):
        return redirect('/user/login/')
    
    return redirect('/user/users/')
