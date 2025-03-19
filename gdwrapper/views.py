from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render

from gdwrapper.services.MongoService import MongoService
from gdwrapper.services.GoogleApiClient import GoogleApiClient

mongo_service = MongoService()

def index(request):
    return render(request, 'frontend/index.html')

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
        client = GoogleApiClient()
        files = client.getAllFiles()
        documents = []
        for f in files:
            doc = {
                "_id": f["id"],
                "name": f.get("name"),
                "mimeType": f.get("mimeType"),
                "size": float(f.get("size", 0)),
                "createdTime": f.get("createdTime"),
                "modifiedTime": f.get("modifiedTime"),
                "ownerEmail": None,
                "capabilities": {},
                "permissions": []
            }
            if "owners" in f and len(f["owners"]) > 0:
                doc["ownerEmail"] = f["owners"][0].get("emailAddress")

            caps = f.get("capabilities", {})
            doc["capabilities"] = {
                "canEdit": caps.get("canEdit", False),
                "canCopy": caps.get("canCopy", False),
                "canComment": caps.get("canComment", False),
                "canDownload": caps.get("canDownload", False),
                "canRename": caps.get("canRename", False),
                "canShare": caps.get("canShare", False)
            }

            perms = f.get("permissions", [])
            doc_perms = []
            for p in perms:
                doc_perms.append({
                    "id": p.get("id"),
                    "type": p.get("type"),
                    "role": p.get("role"),
                    "allowFileDiscovery": p.get("allowFileDiscovery", False),
                    "deleted": p.get("deleted", False),
                    "user": {
                        "id": p.get("emailAddress", ""),
                        "displayName": p.get("displayName", ""),
                        "email": p.get("emailAddress", ""),
                        "photoLink": p.get("photoLink", "")
                    }
                })
            doc["permissions"] = doc_perms
            documents.append(doc)
        return JsonResponse({"status": "Data refreshed successfully"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
