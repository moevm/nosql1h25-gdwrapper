from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import os

from auth.GoogleApiClient import GoogleApiClient
from gdwrapper.services.MongoService import MongoService
from .document_formatter.formatters import formatters_manager
from auth.exceptions import UserNotAuthenticated
from .handlers import refresh_data_in_mongo
from .settings import GD_TOKEN_PATH

from collections import defaultdict

AXIS_TYPES = {
    "mimeType": "categorical",
    "ownerEmail": "categorical",
    "size": "numerical",
    "modifiedTime": "numerical",
}

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
    if os.path.exists(GD_TOKEN_PATH):
        is_authenticated = True

    return render(request, "gdwrapper/index.html", {
        "documents": documents,
        "filters": request.GET,
        'is_authenticated': is_authenticated,
    })


def stats(request):
    is_authenticated = False
    if os.path.exists(GD_TOKEN_PATH):
        is_authenticated = True
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


def determine_chart_type(x_attr, y_attr):
    x_type = AXIS_TYPES.get(x_attr)
    y_type = AXIS_TYPES.get(y_attr)

    if x_type == "categorical" and y_type == "numerical" or x_type == "numerical" and y_type == "categorical":
        return "bar"
    elif x_type == "categorical" and y_type == "categorical":
        return "table"
    elif x_type == "numerical" and y_type == "numerical":
        return "graph"
    else:
        return "error"


def is_numeric(attr, sample_value):
    if attr == "size":
        return True
    if attr == "modifiedTime":
        return True
    return isinstance(sample_value, (int, float))


@require_http_methods(["GET"])
def get_stats_data(request):
    x_attr = request.GET.get('x')
    y_attr = request.GET.get('y')

    if not x_attr or not y_attr or x_attr == y_attr:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    chart_type = determine_chart_type(x_attr, y_attr)
    documents = mongo_service.get_all_documents()

    data = []

    if chart_type == "bar":
        sample_doc = documents[0]
        x_is_numeric = is_numeric(x_attr, sample_doc[x_attr])
        y_is_numeric = is_numeric(y_attr, sample_doc[y_attr])

        if x_is_numeric and not y_is_numeric:
            x_attr, y_attr = y_attr, x_attr

        grouped_data = defaultdict(list)
        for doc in documents:
            key = doc.get(x_attr)
            val = doc.get(y_attr)
            if key is not None and isinstance(val, (int, float)):
                grouped_data[key].append(val)
        data = [{"x": k, "y": sum(v) / len(v)}
                for k, v in grouped_data.items()]

    elif chart_type == "table":
        table = defaultdict(lambda: defaultdict(int))
        for doc in documents:
            row = doc.get(x_attr)
            col = doc.get(y_attr)
            if row is not None and col is not None:
                table[row][col] += 1
        data = [{"row": r, "cols": dict(c)} for r, c in table.items()]

    elif chart_type == "graph":
        if x_attr != "modifiedTime":
            x_attr, y_attr = y_attr, x_attr

        grouped_data = defaultdict(list)
        for doc in documents:
            try:
                x_val = doc.get(x_attr)
                y_val = doc.get(y_attr)
                if not x_val or not isinstance(y_val, (int, float)):
                    continue
                date_key = x_val.split("T")[0]  # только дата
                grouped_data[date_key].append(y_val)
            except Exception:
                continue
        data = [{"x": date, "y": sum(vals)}
                for date, vals in sorted(grouped_data.items())]

    return JsonResponse({"type": chart_type, "data": data})
