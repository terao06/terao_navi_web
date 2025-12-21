from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q, Count
from .models import Company
from .forms import CompanyForm


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
            company = form.save()
            messages.success(request, f'会社「{company.name}」を作成しました。')
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
        company.delete()
        messages.success(request, f'会社「{company_name}」を削除しました。')
        return redirect('company_list')
    
    return render(request, 'admin/companies/company_confirm_delete.html', {'company': company, 'user_count': user_count})


@user_passes_test(is_superuser, login_url='/login/')
def company_detail(request, company_id):
    """会社詳細"""
    company = get_object_or_404(Company, company_id=company_id)
    users = company.users.all().order_by('-created_at')
    
    return render(request, 'admin/companies/company_detail.html', {'company': company, 'users': users})

