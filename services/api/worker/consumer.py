import json
from os import environ as env
from typing import Any, Optional

import pika

from bson.errors import BSONError
from pymongo.errors import PyMongoError
from requests.exceptions import RequestException

from common.mongo.client import MongoDBClient
from common.mongo.models import job as Job
from common.rabbit.client import RabbitMQClient
from worker import scraper, word_histogram

rabbit_client = RabbitMQClient(env["RABBIT_HOST"], env["RABBIT_QUEUE"])
mongo_client = MongoDBClient(env["MONGO_HOST"], env["MONGO_DB"])


def consume() -> None:
    def callback(
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes,
    ) -> None:
        def parse_objectid(body: bytes) -> Optional[Any]:
            try:
                return json.loads(body)["job_id"]
            except (KeyError, json.decoder.JSONDecodeError):
                print(f"Unable to parse job_id from json body({str(body)})", flush=True)
            return None

        def run_job(oid: str) -> Optional[str]:
            try:
                if mongo_client.exists(Job.COLLECTION, oid):
                    job = Job.fetch(mongo_client, oid)
                    word_count = word_histogram.build(scraper.scrape_text(job["url"]))
                    job = Job.complete(mongo_client, oid, word_count)
                    print(f"{json.dumps(job)}", flush=True)
                else:
                    print(
                        f"Unable to find job: job_id({oid}) does not exist", flush=True
                    )
            except BSONError:
                print(f"Unable to find job: job_id({oid}) is malformed", flush=True)
            except (PyMongoError, RequestException, RuntimeError) as e:
                return str(e)
            return None

        def handle_error(oid: str, err_msg: str) -> None:
            try:
                job = Job.fail(mongo_client, oid, err_msg)
                print(f"{json.dumps(job)}", flush=True)
            except PyMongoError:
                print("Unable to call mongo client via Job model", flush=True)

        if oid := parse_objectid(body):
            if err_msg := run_job(oid):
                handle_error(oid, err_msg)

        ch.basic_ack(delivery_tag=method.delivery_tag)  # type: ignore

    rabbit_client.consume(callback)
