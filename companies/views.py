from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import Company
from .forms import CompanyForm
from .dynamodb_utils import (
    generate_client_credentials,
    create_auth_client,
    delete_auth_clients_by_company_id,
)


def is_superuser(user):
    """スーパーユーザーかどうかをチェック"""
    return user.is_authenticated and user.is_superuser


@user_passes_test(is_superuser, login_url='/login/')
def company_list(request):
    """会社一覧"""
    query = request.GET.get('q', '')
    
    # 論理削除されていないユーザーのみカウント
    companies = Company.objects.annotate(
        user_count=Count('users', filter=Q(users__is_deleted=False))
    )
    
    if query:
        companies = companies.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(tel__icontains=query)
        )
    
    context = {
        'companies': companies.order_by('-created_at'),
        'query': query,
    }
    return render(request, 'admin/companies/company_list.html', context)


@user_passes_test(is_superuser, login_url='/login/')
def company_create(request):
    """会社作成"""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            # 会社を作成
            company = form.save()
            
            # クライアント認証情報を生成
            client_id, client_secret, secret_hash = generate_client_credentials()
            
            # DynamoDBに登録
            if create_auth_client(company.company_id, client_id, secret_hash):
                # セッションに認証情報を一時保存（ダウンロード用）
                request.session['new_client_credentials'] = {
                    'company_id': company.company_id,
                    'company_name': company.name,
                    'client_id': client_id,
                    'client_secret': client_secret,
                }
                messages.success(request, f'会社「{company.name}」を作成しました。クライアント認証情報をダウンロードしてください。')
                return redirect('company_credentials_download', company_id=company.company_id)
            else:
                messages.error(request, 'クライアント認証情報の作成に失敗しました。')
                return redirect('company_list')
    else:
        form = CompanyForm()
    
    return render(request, 'admin/companies/company_form.html', {'form': form, 'title': '会社作成'})


@user_passes_test(is_superuser, login_url='/login/')
def company_edit(request, company_id):
    """会社編集"""
    company = get_object_or_404(Company, company_id=company_id)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'会社「{company.name}」を更新しました。')
            return redirect('company_list')
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'admin/companies/company_form.html', {'form': form, 'title': '会社編集', 'company': company})


@user_passes_test(is_superuser, login_url='/login/')
def company_delete(request, company_id):
    """会社削除"""
    company = get_object_or_404(Company, company_id=company_id)
    # 論理削除されていないユーザーのみカウント
    user_count = company.users.filter(is_deleted=False).count()
    
    if request.method == 'POST':
        company_name = company.name
        target_company_id = company.company_id
        
        # Django側の会社削除
        company.delete()
        messages.success(request, f'会社「{company_name}」を削除しました。')

        # DynamoDB側のクライアント認証情報を削除
        deleted = delete_auth_clients_by_company_id(target_company_id)
        if not deleted:
            messages.warning(request, '会社は削除されましたが、DynamoDBのクライアント認証情報の削除に失敗しました。後ほど手動でご確認ください。')

        return redirect('company_list')
    
    return render(request, 'admin/companies/company_confirm_delete.html', {'company': company, 'user_count': user_count})


@user_passes_test(is_superuser, login_url='/login/')
def company_detail(request, company_id):
    """会社詳細"""
    company = get_object_or_404(Company, company_id=company_id)
    users = company.users.all().order_by('-created_at')
    
    return render(request, 'admin/companies/company_detail.html', {'company': company, 'users': users})


@user_passes_test(is_superuser, login_url='/login/')
def company_credentials_download(request, company_id):
    """クライアント認証情報のダウンロードページ"""
    company = get_object_or_404(Company, company_id=company_id)
    
    # セッションから認証情報を取得
    credentials = request.session.get('new_client_credentials')
    
    # セキュリティチェック：対象の会社の認証情報か確認
    if not credentials or credentials.get('company_id') != company_id:
        messages.error(request, '認証情報が見つかりません。すでにダウンロード済みか、セッションが切れた可能性があります。')
        return redirect('company_list')
    
    return render(request, 'admin/companies/company_credentials_download.html', {
        'company': company,
        'credentials': credentials,
    })


@user_passes_test(is_superuser, login_url='/login/')
def company_credentials_json(request, company_id):
    """クライアント認証情報をJSON形式でダウンロード"""
    get_object_or_404(Company, company_id=company_id)
    
    # セッションから認証情報を取得
    credentials = request.session.get('new_client_credentials')
    
    # セキュリティチェック
    if not credentials or credentials.get('company_id') != company_id:
        return JsonResponse({'error': '認証情報が見つかりません'}, status=404)
    
    # セッションから認証情報を削除（一度きり）
    del request.session['new_client_credentials']
    
    # JSON形式でレスポンス
    import json
    from django.http import HttpResponse
    
    response = HttpResponse(
        json.dumps(credentials, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="client_credentials_{company_id}.json"'
    
    return response
