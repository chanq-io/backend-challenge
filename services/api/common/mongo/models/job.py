from enum import Enum
from typing import Any

from common.mongo.client import MongoDBClient

COLLECTION = "jobs"
JobStatus = Enum("JobStatus", "IN_PROGRESS COMPLETE FAIL")


def create(mongodb_client: MongoDBClient, url: str) -> dict[str, Any]:
    oid = mongodb_client.create(
        COLLECTION, {**_status(JobStatus.IN_PROGRESS), "url": url}
    ).inserted_id
    return fetch(mongodb_client, str(oid))


def complete(
    mongodb_client: MongoDBClient, oid: str, word_count: dict[str, Any]
) -> dict[str, Any]:

    mongodb_client.update(
        COLLECTION, oid, {**_status(JobStatus.COMPLETE), "word_count": word_count}
    )
    return fetch(mongodb_client, oid)


def fail(mongodb_client: MongoDBClient, oid: str, error: str) -> dict[str, Any]:
    mongodb_client.update(COLLECTION, oid, {**_status(JobStatus.FAIL), "error": error})
    return fetch(mongodb_client, oid)


def fetch(mongodb_client: MongoDBClient, oid: str) -> dict[str, Any]:
    def public_view(obj) -> dict[str, Any]:
        return {
            **{k: v for k, v in obj.items() if k != "_id"},
            "job_id": str(obj["_id"]),
        }

    return public_view(mongodb_client.retrieve(COLLECTION, oid))


def _status(job_status: JobStatus) -> dict[str, str]:
    return {"status": job_status.name}
