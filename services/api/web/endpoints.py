from os import environ as env
from enum import Enum
from typing import Tuple, Any
from urllib.parse import urlparse

from bson.errors import BSONError
from flask import Flask, jsonify, request, wrappers
from pika.exceptions import AMQPError
from pymongo.errors import PyMongoError

from common.mongo.client import MongoDBClient
from common.mongo.models import job as Job
from common.rabbit.client import RabbitMQClient

server = Flask(__name__)
HealthStatus = Enum("HealthStatus", "PASS FAIL")
ResponseAndCode = Tuple[wrappers.Response, int]
rabbit_client = RabbitMQClient(env["RABBIT_HOST"], env["RABBIT_QUEUE"])
mongo_client = MongoDBClient(env["MONGO_HOST"], env["MONGO_DB"])


@server.route("/health")
def health() -> ResponseAndCode:
    is_healthy = rabbit_client.is_healthy and mongo_client.is_healthy
    healthy_message = "All services are online"
    unhealthy_message = "At least one service is offline"
    status = HealthStatus.PASS if is_healthy else HealthStatus.FAIL
    return _response(
        is_healthy,
        "Completed Health Check",
        {
            "status": status.name,
            "info": healthy_message if is_healthy else unhealthy_message,
        },
        status_code=(200 if is_healthy else 500),
    )


@server.route("/word-count", methods=["GET", "POST"])
def word_count() -> ResponseAndCode:
    def handle_invalid_mime_type() -> ResponseAndCode:
        err = "Please make requests using the application/json MIME type"
        return _response(False, err, status_code=400)

    def handle_dependency_error() -> ResponseAndCode:
        err = "Oh dear! Something unexpected occurred..."
        return _response(False, err, status_code=500)

    def handle_post(request_content: dict) -> ResponseAndCode:
        def is_valid(url: str) -> bool:
            parsed = urlparse(str(url))
            return all([parsed.scheme, parsed.netloc])

        def handle_invalid_input() -> ResponseAndCode:
            err = "You must provide a valid `url` in your POST request JSON"
            return _response(False, err, status_code=400)

        def handle_valid_input(url: str) -> ResponseAndCode:
            def publish_job() -> ResponseAndCode:
                wc_job = Job.create(mongo_client, url)
                job_id = str(wc_job["job_id"])
                rabbit_client.publish({"job_id": job_id})
                return _response(True, f"Scheduled Job: {job_id}", wc_job, 202)

            try:
                return publish_job()
            except (AMQPError, BSONError, PyMongoError):
                return handle_dependency_error()

        url = request_content.get("url", "")
        return handle_valid_input(url) if is_valid(url) else handle_invalid_input()

    def handle_get(request_content: dict) -> ResponseAndCode:
        def is_valid(oid: str) -> bool:
            return bool(oid) and mongo_client.exists(Job.COLLECTION, oid)

        def handle_valid_input(oid: str) -> ResponseAndCode:
            word_count_job = Job.fetch(mongo_client, oid)
            return _response(
                True, f"Fetched Job: {oid}", word_count_job, status_code=200
            )

        def handle_invalid_input() -> ResponseAndCode:
            err = "You must provide a valid `job_id` in your GET request JSON"
            return _response(False, err, status_code=400)

        oid = request_content.get("job_id", "")
        try:
            return handle_valid_input(oid) if is_valid(oid) else handle_invalid_input()
        except (BSONError, PyMongoError):
            return handle_dependency_error()

    if not request.is_json:
        return handle_invalid_mime_type()

    request_content = request.json if request.json is not None else {}
    return {"GET": handle_get, "POST": handle_post}[request.method](request_content)


def _response(
    success: bool, message: str, data: dict[str, Any] = {}, status_code: int = 200
) -> ResponseAndCode:
    return jsonify({"success": success, "message": message, "data": data}), status_code
