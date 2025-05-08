import os

from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from auth.exceptions import UserNotAuthenticated
from gdwrapper.services.MongoService import MongoService
from .document_formatter.formatters import formatters_manager
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
    "table": {"eq": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    "docx": {"eq": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "presentation": {"eq": "application/vnd.google-apps.presentation"},
    "pdf": {"eq": "application/pdf"},
    "image": {"prefix": "image/"},
    "video": {"prefix": "video/"},
    "audio": {"prefix": "audio/"},
}

MIME_LABELS = {
    "docx": "Документ",
    "table": "Таблица",
    "folder": "Папка",
    "document": "Документ",
    "spreadsheet": "Таблица",
    "presentation": "Презентация",
    "pdf": "PDF",
    "image": "Изображение",
    "video": "Видео",
    "audio": "Аудио",
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

    size_from_kb = _clean(request.GET.get("size_from_kb"))
    size_to_kb = _clean(request.GET.get("size_to_kb"))

    sort_field = request.GET.get("sort_field")
    sort_order = request.GET.get("sort_order")

    mime_eq = mime_prefix = None
    if mime_group in MIME_GROUPS:
        mapping = MIME_GROUPS[mime_group]
        mime_eq = mapping.get("eq")
        mime_prefix = mapping.get("prefix")

    has_filter = any([
        mime_eq, mime_prefix, name, owner_email,
        created_from, created_to, modified_from, modified_to,
        size_from_kb, size_to_kb
    ])

    if has_filter:
        documents = mongo_service.get_documents(
            mime_eq=mime_eq,
            mime_prefix=mime_prefix,
            name=name,
            created_from=created_from,
            created_to=created_to,
            modified_from=modified_from,
            modified_to=modified_to,
            size_min=size_from_kb,
            size_max=size_to_kb,
            owner_email=owner_email,
            sort_field=sort_field,
            sort_order=sort_order,
        )
    else:
        documents = mongo_service.get_documents(
            sort_field=sort_field,
            sort_order=sort_order,
        )

    for doc in documents:
        doc["id"] = str(doc.get("_id", ""))
        formatters_manager.apply_formatters(doc)

        real_mt = doc.get("mimeType", "")
        label = None

        for key, mapping in MIME_GROUPS.items():
            if mapping.get("eq") and mapping["eq"] == real_mt:
                label = MIME_LABELS[key]
                break
            if mapping.get("prefix") and real_mt.startswith(mapping["prefix"]):
                label = MIME_LABELS[key]
                break

        if not label:
            label = "Прочее"

        doc["typeLabel"] = label

    is_authenticated = os.path.exists(GD_TOKEN_PATH)
    return render(request, "gdwrapper/index.html", {
        "documents": documents,
        "filters": request.GET,
        "is_authenticated": is_authenticated,
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
