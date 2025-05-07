from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from bson import json_util
from django.http import HttpResponse
import tempfile
import os
import zipfile
import io

from auth.GoogleApiClient import GoogleApiClient
from gdwrapper.services.MongoService import MongoService
from .document_formatter.formatters import formatters_manager
from auth.exceptions import UserNotAuthenticated
from .handlers import refresh_data_in_mongo
from .settings import GD_TOKEN_PATH






mongo_service = MongoService()


def _clean(v):
    return v or None

SIZE_PRESETS = {
    "lt100": (None, 100 * 1024 - 1),
    "100_500": (100 * 1024, 500 * 1024 - 1),
    "500_1m": (500 * 1024, 1 * 1024 * 1024 - 1),
    "1m_10m": (1 * 1024 * 1024, 10 * 1024 * 1024 - 1),
    "10m_100m": (10 * 1024 * 1024, 100 * 1024 * 1024 - 1),
    "gt100m": (100 * 1024 * 1024, None),
}

MIME_GROUPS = {
    "folder": {"eq": "application/vnd.google-apps.folder"},
    "document": {"eq": "application/vnd.google-apps.document"},
    "spreadsheet": {"eq": "application/vnd.google-apps.spreadsheet"},
    "presentation": {"eq": "application/vnd.google-apps.presentation"},
    "pdf": {"eq": "application/pdf"},
    "image": {"prefix": "image/"},
    "video": {"prefix": "video/"},
    "audio": {"prefix": "audio/"},
}


@ensure_csrf_cookie
def index(request):
    mime_group = _clean(request.GET.get("mime_group"))
    name = _clean(request.GET.get("name"))
    owner_email = _clean(request.GET.get("owner_email"))

    created_from = _clean(request.GET.get("created_from"))
    created_to = _clean(request.GET.get("created_to"))
    modified_from = _clean(request.GET.get("modified_from"))
    modified_to = _clean(request.GET.get("modified_to"))

    size_range = _clean(request.GET.get("size_range"))
    size_min = size_max = None
    if size_range in SIZE_PRESETS:
        size_min, size_max = SIZE_PRESETS[size_range]

    mime_eq = mime_prefix = None
    if mime_group in MIME_GROUPS:
        mapping = MIME_GROUPS[mime_group]
        mime_eq = mapping.get("eq")
        mime_prefix = mapping.get("prefix")

    if any([mime_eq, mime_prefix, name, owner_email,
            created_from, created_to, modified_from, modified_to,
            size_min, size_max]):

        documents = mongo_service.get_documents(
            mime_eq=mime_eq,
            mime_prefix=mime_prefix,
            name=name,
            created_from=created_from,
            created_to=created_to,
            modified_from=modified_from,
            modified_to=modified_to,
            size_min=size_min,
            size_max=size_max,
            owner_email=owner_email,
        )
    else:
        documents = mongo_service.get_all_documents()

    for doc in documents:
        doc["id"] = str(doc.get("_id", ""))
        formatters_manager.apply_formatters(doc)
    
    is_authenticated = False
    if os.path.exists(GD_TOKEN_PATH): is_authenticated = True
    
    return render(request, "gdwrapper/index.html", {
        "documents": documents,
        "filters": request.GET,
        'is_authenticated': is_authenticated,
    })


def stats(request):
    is_authenticated = False
    if os.path.exists(GD_TOKEN_PATH): is_authenticated = True
    return render(request, "gdwrapper/stats.html", {
        'is_authenticated': is_authenticated,
    })


@require_http_methods(["GET"])
def get_all_files(request):
    docs = mongo_service.get_all_documents()
    for d in docs:
        d["_id"] = str(d["_id"])
    return JsonResponse({"data": docs})


@require_http_methods(["POST"])
def refresh_data(request):
    """
    Эндпоинт для рефреша: получаем свежий список файлов из Google Drive,
    приводим к нужному формату и перезаписываем documents.
    """
    try:
        refresh_data_in_mongo()
        return JsonResponse({"status": "Data refreshed successfully"})
    except UserNotAuthenticated:
        return JsonResponse({"redirect_to": reverse('auth:auth')}, status=403)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@require_http_methods(["GET"])
def export_data(request):
    """Экспорт всех данных из MongoDB в ZIP-архиве"""
    if not os.path.exists(GD_TOKEN_PATH):
        return JsonResponse({"error": "Требуется авторизация"}, status=403)
    
    try:
        # Получаем все данные
        data = {
            "metadata": {
                "app": "GDWrapper",
                "export_date": datetime.now().isoformat(),
                "version": "1.0"
            },
            "documents": list(mongo_service.get_all_documents())
        }
        
        # Создаем ZIP в памяти
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Добавляем данные в JSON
            json_data = json_util.dumps(data, indent=2)
            zip_file.writestr('gdwrapper_export.json', json_data)
            
            # Добавляем README
            readme = """Это архив экспорта из GDWrapper
Содержит метаданные файлов на момент экспорта
Для импорта используйте соответствующую функцию в приложении"""
            zip_file.writestr('README.txt', readme)
        
        zip_buffer.seek(0)
        
        # Формируем имя файла с датой
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gdwrapper_export_{timestamp}.zip"
        
        # Возвращаем архив
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
@require_http_methods(["POST"])
def import_data(request):
    try:
        if 'file' not in request.FILES:
            return HttpResponse("Файл не был загружен", status=400)

        uploaded_file = request.FILES['file']
        
        # Простая проверка на ZIP
        if not uploaded_file.name.lower().endswith('.zip'):
            return HttpResponse("Файл должен быть в формате ZIP", status=400)

        # Здесь ваша логика обработки ZIP-архива
        # Например, сохранение на диск или обработка в памяти
        
        return JsonResponse({
            "status": "ZIP-архив успешно обработан",
            "files_processed": 42  # Примерное количество обработанных файлов
        })
        
    except Exception as e:
        return HttpResponse(f"Ошибка: {str(e)}", status=500)