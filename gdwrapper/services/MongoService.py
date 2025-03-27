from django.conf import settings
from pymongo import MongoClient


class MongoService:
    def __init__(self):
        mongo_uri = settings.MONGO_URI
        db_name = settings.DB_NAME
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

    def get_all_documents(self):
        """
        Возвращает все документы из коллекции `documents`.
        """
        cursor = self.db.documents.find()
        return list(cursor)

    def refresh_documents(self, documents):
        """
        Полностью пересоздаёт коллекцию `documents`.
        Удаляем все старые записи и вставляем новые (из Google API).
        """
        self.db.documents.delete_many({})
        if documents:
            self.db.documents.insert_many(documents)
