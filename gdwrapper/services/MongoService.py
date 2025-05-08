import os
import re
from typing import Optional, Union, List, Dict, Any
from datetime import datetime

from django.conf import settings
from pymongo import MongoClient


class MongoService:
    def __init__(self) -> None:
        mongo_uri = getattr(settings, "MONGO_URI",
                            os.getenv("MONGO_URI", "mongodb://mongo:27017"))
        db_name = getattr(settings, "DB_NAME",
                          os.getenv("MONGO_DB", "gdwrapper"))
        coll_name = getattr(settings, "COLL_NAME",
                            os.getenv("MONGO_COLLECTION", "documents"))

        self.col = (
            MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            [db_name][coll_name]
        )

    @staticmethod
    def _to_float(v: Union[str, float, None]) -> Optional[float]:
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _iso_bound(date_str: Optional[str], *, end: bool = False) -> Optional[str]:
        if not date_str:
            return None
        if "T" in date_str:
            return date_str
        suffix = "T23:59:59Z" if end else "T00:00:00Z"
        return f"{date_str}{suffix}"

    def get_all_documents(self) -> List[Dict]:
        return list(self.col.find({}))

    def get_documents(
            self,
            *,
            mime_eq: Optional[str] = None,
            mime_prefix: Optional[str] = None,
            name: Optional[str] = None,
            created_from: Optional[str] = None,
            created_to: Optional[str] = None,
            modified_from: Optional[str] = None,
            modified_to: Optional[str] = None,
            size_min: Union[str, float, None] = None,
            size_max: Union[str, float, None] = None,
            owner_email: Optional[str] = None,
    ) -> List[Dict]:

        q: Dict = {}

        # MIME
        if mime_eq:
            q["mimeType"] = mime_eq
        elif mime_prefix:
            q["mimeType"] = {"$regex": f"^{re.escape(mime_prefix)}"}

        if name:
            q["name"] = {"$regex": name, "$options": "i"}

        created_cond = {}
        cf = self._iso_bound(created_from)
        ct = self._iso_bound(created_to, end=True)
        if cf:
            created_cond["$gte"] = cf
        if ct:
            created_cond["$lte"] = ct
        if created_cond:
            q["createdTime"] = created_cond

        modified_cond = {}
        mf = self._iso_bound(modified_from)
        mt = self._iso_bound(modified_to, end=True)
        if mf:
            modified_cond["$gte"] = mf
        if mt:
            modified_cond["$lte"] = mt
        if modified_cond:
            q["modifiedTime"] = modified_cond

        size_cond = {}
        _min = self._to_float(size_min)
        _max = self._to_float(size_max)
        if _min is not None:
            size_cond["$gte"] = _min
        if _max is not None:
            size_cond["$lte"] = _max
        if size_cond:
            q["size"] = size_cond

        if owner_email:
            q["ownerEmail"] = owner_email

        return list(self.col.find(q))
    
    def add_document(self, file_data: Dict[str, Any]) -> str:
        """
        Добавляет один файл в коллекцию
        :param file_data: Словарь с данными о файле
        :return: ID добавленного документа (строка)
        """
        
        result = self.col.insert_one(file_data)
        return str(result.inserted_id)

    def add_documents(self, files_data: List[Dict[str, Any]]) -> List[str]:
        """
        Добавляет несколько файлов в коллекцию
        :param files_data: Список словарей с данными о файлах
        :return: Список ID добавленных документов (строки)
        """
        if not files_data:
            return []
            
        result = self.col.insert_many(files_data)
        return [str(id) for id in result.inserted_ids]

    def refresh_documents(self, docs: List[Dict]) -> None:
        self.col.delete_many({})
        if docs:
            self.col.insert_many(docs)
