from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.core.files.base import ContentFile
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from bson import json_util
from django.http import HttpResponse
from datetime import datetime
import pymongo

import tempfile
import os
import zipfile
import io
import json

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
        if id not in doc:
            doc['id'] = doc['_id']
        if "modifiedTime" not in doc:
            doc["modifiedTime "] = 1
    
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
    """Экспорт данных в JSON (без ZIP)"""
    try:
        if not os.path.exists(GD_TOKEN_PATH):
            return JsonResponse({"error": "Требуется авторизация"}, status=403)
        
        documents = list(mongo_service.get_all_documents())
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gdwrapper_export_{timestamp}.json"
        
        json_data = json_util.dumps({
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "app_name": "GDWrapper",
                "document_count": len(documents)
            },
            "documents": documents
        }, indent=2)
        
        # Возвращаем JSON файл
        response = HttpResponse(json_data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["POST"])
def import_data(request):
    """Обработчик импорта JSON файла с использованием MongoService"""
    try:
        if os.path.exists(GD_TOKEN_PATH):
            return JsonResponse({"error": "Импорт доступен только без авторизации"}, status=403)

        if 'file' not in request.FILES:
            return JsonResponse({"error": "Файл не был загружен"}, status=400)

        uploaded_file = request.FILES['file']
        
        if not uploaded_file.name.lower().endswith('.json'):
            return JsonResponse({"error": "Требуется файл в формате JSON"}, status=400)

        try:
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            
            if not isinstance(data, dict) or 'documents' not in data:
                raise ValueError("Некорректный формат данных. Ожидается объект с полем 'documents'")

            mongo_service = MongoService()
            
            valid_documents = []
            errors = []
            
            for i, doc in enumerate(data['documents']):
                try:
                    if not isinstance(doc, dict):
                        raise ValueError("Документ должен быть объектом")
                    
                    if '_id' not in doc:
                        raise ValueError("Отсутствует обязательное поле '_id'")
                    
                    valid_documents.append(doc)
                except Exception as e:
                    errors.append(f"Документ {i}: {str(e)}")

            if not valid_documents:
                raise ValueError("Нет валидных документов для импорта")

            imported_ids = []
            updated_count = 0
            
            for doc in valid_documents:
                try:
                    doc_id = mongo_service.add_document(doc)
                    imported_ids.append(doc_id)
                except pymongo.errors.DuplicateKeyError:
                    result = mongo_service.col.replace_one(
                        {'_id': doc['_id']},
                        doc
                    )
                    if result.modified_count > 0:
                        updated_count += 1

            response_data = {
                "status": "success",
                "imported": len(imported_ids),
                "updated": updated_count,
                "total_processed": len(data['documents'])
            }

            if errors:
                response_data["status"] = "partial"
                response_data["error_count"] = len(errors)
                response_data["sample_errors"] = errors[:3]
                return JsonResponse(response_data, status=207)
            
            return JsonResponse(response_data)

        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Ошибка в JSON-файле: {str(e)}"}, status=400)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except UnicodeDecodeError:
            return JsonResponse({"error": "Ошибка декодирования файла. Убедитесь, что файл в UTF-8"}, status=400)
        except pymongo.errors.ConnectionError as e:
            return JsonResponse({"error": f"Ошибка подключения к MongoDB: {str(e)}"}, status=503)
        except Exception as e:
            return JsonResponse({"error": f"Ошибка сервера: {str(e)}"}, status=500)
            
    except Exception as e:
        return JsonResponse({"error": f"Непредвиденная ошибка: {str(e)}"}, status=500)