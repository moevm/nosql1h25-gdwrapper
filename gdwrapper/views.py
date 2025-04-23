from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from auth.GoogleApiClient import GoogleApiClient
from gdwrapper.services.MongoService import MongoService
from .document_formatter.formatters import formatters_manager

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

    return render(request, "gdwrapper/index.html", {
        "documents": documents,
        "filters": request.GET,
    })


def stats(request):
    return render(request, "gdwrapper/stats.html")


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
        client = GoogleApiClient()
        files = client.getAllFiles()
        documents = []

        for f in files:
            doc = {
                "_id": f["id"],
                "id": f["id"],
                "name": f.get("name"),
                "mimeType": f.get("mimeType"),
                "size": float(f.get("size", 0)),
                "createdTime": f.get("createdTime"),
                "modifiedTime": f.get("modifiedTime"),
                "ownerEmail": None,
                "capabilities": {},
                "permissions": [],
            }

            if f.get("owners"):
                doc["ownerEmail"] = f["owners"][0].get("emailAddress")

            caps = f.get("capabilities", {})
            doc["capabilities"] = {
                "canEdit": caps.get("canEdit", False),
                "canCopy": caps.get("canCopy", False),
                "canComment": caps.get("canComment", False),
                "canDownload": caps.get("canDownload", False),
                "canRename": caps.get("canRename", False),
                "canShare": caps.get("canShare", False),
            }

            doc["permissions"] = [
                {
                    "id": p.get("id"),
                    "type": p.get("type"),
                    "role": p.get("role"),
                    "allowFileDiscovery": p.get("allowFileDiscovery", False),
                    "deleted": p.get("deleted", False),
                    "user": {
                        "id": p.get("emailAddress", ""),
                        "displayName": p.get("displayName", ""),
                        "email": p.get("emailAddress", ""),
                        "photoLink": p.get("photoLink", ""),
                    },
                }
                for p in f.get("permissions", [])
            ]

            documents.append(doc)

        mongo_service.refresh_documents(documents)
        return JsonResponse({"status": "Data refreshed successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
