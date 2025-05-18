from auth.GoogleApiClient import GoogleApiClient
from gdwrapper.services.MongoService import MongoService

def refresh_data_in_mongo():
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
            "permissions": [],
            "parents": f.get("parents")
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
        mongo_service = MongoService()
        mongo_service.refresh_documents(documents)