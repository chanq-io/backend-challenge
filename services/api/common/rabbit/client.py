import json

from typing import Any, Callable, Tuple

from pika.exceptions import AMQPError
import pika


class RabbitMQClient:
    def __init__(self, host: str, queue: str):
        self._connection_parameters = pika.ConnectionParameters(host=host)
        self._queue = queue

    def publish(self, body: dict[str, Any]) -> None:
        connection, channel = self._create_connection_and_channel()
        self._create_queue(channel)
        props = pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)
        channel.basic_publish(
            exchange="",
            routing_key=self._queue,
            body=bytes(json.dumps(body), encoding="raw_unicode_escape"),
            properties=props,
        )
        connection.close()

    def consume(
        self,
        callback: Callable[
            [
                pika.adapters.blocking_connection.BlockingChannel,
                pika.spec.Basic.Deliver,
                pika.spec.BasicProperties,
                bytes,
            ],
            None,
        ],
    ) -> None:
        connection, channel = self._create_connection_and_channel()
        self._create_queue(channel)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=self._queue, on_message_callback=callback)
        channel.start_consuming()

    @property
    def is_healthy(self) -> bool:
        try:
            connection, channel = self._create_connection_and_channel()
            return all(not e for e in [connection.is_closed, channel.is_closed])
        except AMQPError:
            return False

    def _create_queue(
        self, channel: pika.adapters.blocking_connection.BlockingChannel
    ) -> None:
        channel.queue_declare(queue=self._queue, durable=True)

    def _create_connection_and_channel(
        self,
    ) -> Tuple[
        pika.adapters.blocking_connection.BlockingConnection,
        pika.adapters.blocking_connection.BlockingChannel,
    ]:
        connection = pika.BlockingConnection(self._connection_parameters)
        return connection, connection.channel()
