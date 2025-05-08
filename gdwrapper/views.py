from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import os

from auth_google.GoogleApiClient import GoogleApiClient
from gdwrapper.services.MongoService import MongoService
from .document_formatter.formatters import formatters_manager
from auth_google.exceptions import UserNotAuthenticated
from .handlers import refresh_data_in_mongo
from .settings import GD_TOKEN_PATH
from auth_google.GoogleApiClient import GoogleApiClient
from .imdict import imdict
from copy import deepcopy
import json


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
    
    is_authenticated = False
    if os.path.exists(GD_TOKEN_PATH): is_authenticated = True
    try:
        root_dir_id = GoogleApiClient().getRootFolderID()
    except UserNotAuthenticated:
        return render(request, "gdwrapper/index.html", {
            "tree": {},
            "parent": None,
            "filters": request.GET,
            'is_authenticated': False,
        })
    tree = {}
    for doc in documents:
        comment = mongo_service.get_comment(doc['id'])
        if comment is not None:
            doc['comment'] = comment['text']
        doc['_id'] = str(doc['_id'])
        formatters_manager.apply_formatters(doc)
        if doc['parent'] == None:
            tree.setdefault(root_dir_id, set([])).add(imdict(doc))
        else: tree.setdefault(doc['parent'], set([])).add(imdict(doc))
        current_doc = deepcopy(doc)
        while current_doc['parent'] is not None and current_doc['parent'] != root_dir_id:
            parent_doc = mongo_service.get_document(current_doc['parent'])
            if parent_doc is None:
                break
            parent_doc['_id'] = str(parent_doc['_id'])
            formatters_manager.apply_formatters(parent_doc)
            comment = mongo_service.get_comment(parent_doc['id'])
            if comment is not None:
                parent_doc['comment'] = comment['text']
            tree.setdefault(parent_doc['parent'], set([])).add(imdict(parent_doc))
            current_doc = deepcopy(parent_doc)
        if doc['mimeType'] == 'application/vnd.google-apps.folder':
            documents.extend(mongo_service.find({'parent': doc['id']}))
            
    return render(request, "gdwrapper/index.html", {
        "tree": tree,
        "parent": root_dir_id,
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
    

@require_http_methods(["POST"])
def create_or_update_comment(request):
    mongo_service.create_or_update_comment(**json.loads(request.body.decode("utf-8")))
    return JsonResponse({"status": "Comment created successfully"})
