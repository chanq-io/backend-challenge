from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.results import InsertOneResult, UpdateResult
from typing import Optional, Any
from bson.objectid import ObjectId as OID


class MongoDBClient:
    def __init__(self, host: str, db: str):
        self.client: MongoClient = MongoClient(host, 27017)
        self.db = self.client[db]

    def create(self, collection: str, document: dict[str, Any]) -> InsertOneResult:
        return self.db[collection].insert_one(document)

    def update(
        self, collection: str, oid: str, updates: dict[str, Any]
    ) -> UpdateResult:

        return self.db[collection].update_one(self._id_query(oid), {"$set": updates})

    def retrieve(self, collection: str, oid: str) -> Optional[Any]:
        return self.db[collection].find_one(OID(oid))

    def exists(self, collection: str, oid: str) -> bool:
        return bool(self.db[collection].count_documents(self._id_query(oid), limit=1))

    @property
    def is_healthy(self) -> bool:
        try:
            return bool(self.client.server_info())
        except ServerSelectionTimeoutError:
            return False

    def _id_query(self, oid) -> dict[str, OID]:
        return {"_id": OID(oid)}
