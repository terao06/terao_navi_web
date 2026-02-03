from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Manual
from .forms import ManualForm
from .s3_utils import upload_file_to_s3, download_file_from_s3, delete_file_from_s3, get_file_url
import logging

logger = logging.getLogger(__name__)


def get_s3_key(manual):
    """マニュアルのS3キーを生成"""
    return f"{manual.application.company_id}/{manual.application.application_id}/{manual.manual_id}.{manual.file_extension}"


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
def manual_list(request):
    """マニュアル一覧（同一company_id内のみ）"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    query = request.GET.get('q', '')
    manuals = Manual.objects.filter(application__company_id=current_user.company_id).select_related('application', 'application__company')
    
    if query:
        manuals = manuals.filter(
            Q(manual_name__icontains=query) |
            Q(description__icontains=query) |
            Q(application__application_name__icontains=query)
        )
    
    context = {
        'manuals': manuals.order_by('-created_at'),
        'query': query,
        'current_user': current_user,
    }
    return render(request, 'user/manuals/manual_list.html', context)


@require_user_authentication
@never_cache
@ensure_csrf_cookie
def manual_create(request):
    """マニュアル作成"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    # 書き込み権限チェック（READ_ONLYは不可）
    if current_user.role_id == 3:  # READ_ONLY
        messages.error(request, 'マニュアルを作成する権限がありません。')
        return redirect('manual_list')
    
    if request.method == 'POST':
        logger.info("マニュアル登録を開始します。")
        form = ManualForm(request.POST, request.FILES, current_user=current_user)
        if form.is_valid():
            manual = form.save(commit=False)
            
            # PDFファイルをS3にアップロード
            pdf_file = form.cleaned_data['pdf_file']
            application = form.cleaned_data['application']
            
            try:
                # ファイル拡張子を取得（例: "pdf"）
                file_extension = pdf_file.name.split('.')[-1].lower()
                manual.file_extension = file_extension
                manual.file_size = pdf_file.size
                
                # まず保存してmanual_idを取得
                manual.save()
                
                # manual_id.pdfとしてS3にアップロード
                filename = f"{manual.manual_id}.{file_extension}"
                upload_file_to_s3(
                    pdf_file.file,
                    application.company_id,
                    application.application_id,
                    filename
                )
                # ベクトルデータをPostgreSQL(PGVector)へ登録（設定されている場合のみ）
                s3_key = f"{application.company_id}/{application.application_id}/{filename}"
                try:
                    from .vector_ingest import ingest_manual_to_vector_store

                    ingest_manual_to_vector_store(
                        manual_id=manual.manual_id,
                        company_id=application.company_id,
                        application_id=application.application_id,
                        s3_key=s3_key,
                        title=manual.manual_name,
                    )
                except Exception as e:
                    logger.exception("ベクトル登録に失敗しました: %s", e)
                    messages.warning(request, f'ベクトル登録に失敗しました（検索機能に影響する可能性があります）: {str(e)}')
                logger.info("マニュアル登録が成功しました。")
                messages.success(request, f'マニュアル「{manual.manual_name}」を作成しました。')
                return redirect('manual_list')
            except Exception as e:
                logger.error(f"ファイルのアップロードに失敗しました: {str(e)}")
                messages.error(request, f'ファイルのアップロードに失敗しました: {str(e)}')
    else:
        form = ManualForm(current_user=current_user)

    return render(request, 'user/manuals/manual_form.html', {
        'form': form,
        'title': 'マニュアル作成',
        'current_user': current_user,
        'manual': None,
    })


@require_user_authentication
@never_cache
@ensure_csrf_cookie
def manual_edit(request, manual_id):
    """マニュアル編集"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    # 書き込み権限チェック（READ_ONLYは不可）
    if current_user.role_id == 3:  # READ_ONLY
        messages.error(request, 'マニュアルを編集する権限がありません。')
        return redirect('manual_list')
    
    manual = get_object_or_404(Manual, manual_id=manual_id, application__company_id=current_user.company_id)

    # 更新前のS3キー（=source）を保持（application変更があっても古いキーを消せるように）
    old_company_id = manual.application.company_id
    old_application_id = manual.application.application_id
    old_file_extension = manual.file_extension
    
    if request.method == 'POST':
        form = ManualForm(request.POST, request.FILES, instance=manual, current_user=current_user)
        if form.is_valid():
            manual = form.save(commit=False)
            application = form.cleaned_data['application']
            
            # 新しいPDFファイルがアップロードされた場合
            pdf_file = form.cleaned_data.get('pdf_file')
            if pdf_file:
                try:
                    # 古いファイル/ベクトルを削除（差し替え時に残骸が残らないように）
                    old_s3_key = f"{old_company_id}/{old_application_id}/{manual.manual_id}.{old_file_extension}"
                    try:
                        delete_file_from_s3(old_s3_key)
                    except:
                        pass  # 削除失敗しても続行

                    try:
                        from .vector_ingest import delete_manual_from_vector_store

                        delete_manual_from_vector_store(s3_key=old_s3_key)
                    except Exception as e:
                        logger.exception("ベクトル削除に失敗しました: %s", e)
                        messages.warning(request, f'ベクトル削除に失敗しました（検索機能に影響する可能性があります）: {str(e)}')
                    
                    # ファイル拡張子を取得して更新
                    file_extension = pdf_file.name.split('.')[-1].lower()
                    manual.file_extension = file_extension
                    manual.file_size = pdf_file.size
                    
                    # manual_id.{拡張子}としてアップロード
                    filename = f"{manual.manual_id}.{file_extension}"
                    upload_file_to_s3(
                        pdf_file.file,
                        application.company_id,
                        application.application_id,
                        filename
                    )
                    # ベクトルデータをPostgreSQL(PGVector)へ登録（設定されている場合のみ）
                    try:
                        s3_key = f"{application.company_id}/{application.application_id}/{filename}"
                        from .vector_ingest import ingest_manual_to_vector_store

                        ingest_manual_to_vector_store(
                            manual_id=manual.manual_id,
                            company_id=application.company_id,
                            application_id=application.application_id,
                            s3_key=s3_key,
                            title=manual.manual_name,
                        )
                    except Exception as e:
                        logger.exception("ベクトル登録に失敗しました: %s", e)
                        messages.warning(request, f'ベクトル登録に失敗しました（検索機能に影響する可能性があります）: {str(e)}')
            
                except Exception as e:
                    messages.error(request, f'ファイルのアップロードに失敗しました: {str(e)}')
                    return render(request, 'user/manuals/manual_form.html', {
                        'form': form,
                        'title': 'マニュアル編集',
                        'manual': manual,
                        'current_user': current_user,
                    })
            
            manual.save()
            messages.success(request, f'マニュアル「{manual.manual_name}」を更新しました。')
            return redirect('manual_list')
    else:
        form = ManualForm(instance=manual, current_user=current_user)
    
    return render(request, 'user/manuals/manual_form.html', {
        'form': form,
        'title': 'マニュアル編集',
        'manual': manual,
        'current_user': current_user,
    })


@require_user_authentication
@never_cache
@ensure_csrf_cookie
def manual_delete(request, manual_id):
    """マニュアル削除"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    # 書き込み権限チェック（READ_ONLYは不可）
    if current_user.role_id == 3:  # READ_ONLY
        messages.error(request, 'マニュアルを削除する権限がありません。')
        return redirect('manual_list')
    
    manual = get_object_or_404(Manual, manual_id=manual_id, application__company_id=current_user.company_id)
    
    if request.method == 'POST':
        manual_name = manual.manual_name

        # ベクトルDB側も削除（設定されている場合のみ）
        try:
            s3_key = get_s3_key(manual)
            from .vector_ingest import delete_manual_from_vector_store

            delete_manual_from_vector_store(s3_key=s3_key)
        except Exception as e:
            logger.exception("ベクトル削除に失敗しました: %s", e)
            messages.warning(request, f'ベクトル削除に失敗しました（検索機能に影響する可能性があります）: {str(e)}')
        
        # 論理削除（S3のファイルは削除しない）
        manual.delete()
        
        messages.success(request, f'マニュアル「{manual_name}」を削除しました。')
        return redirect('manual_list')
    
    return render(request, 'user/manuals/manual_delete.html', {
        'manual': manual,
        'current_user': current_user,
    })


@require_user_authentication
def manual_detail(request, manual_id):
    """マニュアル詳細"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    manual = get_object_or_404(Manual, manual_id=manual_id, application__company_id=current_user.company_id)
    
    return render(request, 'user/manuals/manual_detail.html', {
        'manual': manual,
        'current_user': current_user,
    })


@require_user_authentication
@xframe_options_exempt
def manual_preview(request, manual_id):
    """マニュアルプレビュー"""
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, 'ユーザー情報が見つかりません。')
        return redirect('/user/login/')
    
    manual = get_object_or_404(Manual, manual_id=manual_id, application__company_id=current_user.company_id)
    
    try:
        # S3キーを生成してファイルを取得
        s3_key = get_s3_key(manual)
        file_content = download_file_from_s3(s3_key)
        
        # PDFとして表示（ダウンロードではなくインライン表示）
        filename = f"{manual.manual_id}.{manual.file_extension}"
        response = HttpResponse(file_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    except Exception as e:
        messages.error(request, f'ファイルのプレビューに失敗しました: {str(e)}')
        return redirect('manual_detail', manual_id=manual_id)
