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


mongo_service = MongoService()

@ensure_csrf_cookie
def index(request):
    documents = mongo_service.get_all_documents()
    for document in documents: formatters_manager.apply_formatters(document)
    is_authenticated = False
    if os.path.exists(GD_TOKEN_PATH): is_authenticated = True
    return render(request, 'gdwrapper/index.html', {'documents': documents, 'is_authenticated': is_authenticated})


def stats(request):
    return render(request, 'gdwrapper/stats.html')


@require_http_methods(["GET"])
def get_all_files(request):
    """
    Эндпоинт для получения всех документов из MongoDB.
    """
    docs = mongo_service.get_all_documents()
    for d in docs:
        d["_id"] = str(d["_id"])
    return JsonResponse({"data": docs}, safe=False)


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
