from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ScriptTagForm


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
def generate_script_tag(request):
    """スクリプトタグ生成"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    generated_tag = None
    
    if request.method == 'POST':
        form = ScriptTagForm(request.POST)
        
        if form.is_valid():
            # company_idを取得
            company_id = current_user.company_id
            
            chat_title = form.cleaned_data['chat_title']
            chat_color = form.cleaned_data['chat_color']
            
            # スクリプトタグを生成
            generated_tag = f'''<script
  src="http://localhost:3000/chat.js"
  data-company-id="{company_id}"
  data-chat-title="{chat_title}"
  data-chat-color="{chat_color}"
></script>'''
    else:
        form = ScriptTagForm()
        company_id = None
        chat_title = None
        chat_color = None
    
    # プレビュー用のパラメータを渡す
    if request.method == 'POST' and form.is_valid():
        company_id = current_user.company_id
        chat_title = form.cleaned_data['chat_title']
        chat_color = form.cleaned_data['chat_color']
    else:
        company_id = None
        chat_title = None
        chat_color = None
    
    return render(request, 'user/tags/script_tag_generator.html', {
        'form': form,
        'generated_tag': generated_tag,
        'current_user': current_user,
        'company_id': company_id,
        'chat_title': chat_title,
        'chat_color': chat_color,
    })
