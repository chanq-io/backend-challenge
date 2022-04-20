import pytest
import pika
from common.rabbit.client import RabbitMQClient


def test_construction(mocker):
    fake_host, fake_queue = "host", "queue"
    fake_connection_params = "connect_to_something"
    mock_pika = mocker.patch("common.rabbit.client.pika")
    mock_pika.ConnectionParameters.return_value = fake_connection_params

    client = RabbitMQClient(fake_host, fake_queue)

    mock_pika.ConnectionParameters.assert_called_once_with(host=fake_host)
    assert client._connection_parameters == fake_connection_params
    assert client._queue == fake_queue


def test_publish(mocker):
    fake_connection_params, fake_properties = "connect_to_something", "properties"
    fake_queue, fake_body, fake_delivery_mode = "queue", {"a": "b"}, "deliver"
    mock_pika = mocker.patch("common.rabbit.client.pika")
    mock_pika.spec.PERSISTENT_DELIVERY_MODE = fake_delivery_mode
    mock_pika.BasicProperties.return_value = fake_properties
    client = RabbitMQClient("whatever", fake_queue)
    client._connection_parameters = fake_connection_params

    client.publish(fake_body)

    mock_pika.BasicProperties.assert_called_once_with(delivery_mode=fake_delivery_mode)
    mock_pika.BlockingConnection.assert_called_once_with(fake_connection_params)
    mock_connection = mock_pika.BlockingConnection.return_value
    mock_connection.channel.assert_called_once()
    mock_connection.close.assert_called_once()
    mock_channel = mock_connection.channel.return_value
    mock_channel.queue_declare.assert_called_once_with(queue=fake_queue, durable=True)
    mock_channel.basic_publish.assert_called_once_with(
        exchange="",
        routing_key=fake_queue,
        body=b'{"a": "b"}',
        properties=fake_properties,
    )


def test_consume(mocker):
    fake_connection_params, fake_callback = "connect_to_something", "a_function"
    fake_queue = "queue"
    mock_pika = mocker.patch("common.rabbit.client.pika")
    client = RabbitMQClient("whatever", fake_queue)
    client._connection_parameters = fake_connection_params

    client.consume(fake_callback)

    mock_pika.BlockingConnection.assert_called_once_with(fake_connection_params)
    mock_connection = mock_pika.BlockingConnection.return_value
    mock_connection.channel.assert_called_once()
    mock_channel = mock_connection.channel.return_value
    mock_channel.queue_declare.assert_called_once_with(queue=fake_queue, durable=True)
    mock_channel.basic_qos.assert_called_once_with(prefetch_count=1)
    mock_channel.basic_consume(queue=fake_queue, on_message_callback=fake_callback)
    mock_channel.start_consuming.assert_called_once()


def test_is_healthy(mocker):
    (
        client,
        mock_pika,
        mock_connection,
        fake_connection_params,
    ) = _setup_health_check_test(mocker)
    assert client.is_healthy

    mock_pika.BlockingConnection.assert_called_once_with(fake_connection_params)
    mock_connection.channel.assert_called_once()


def test_is_unhealthy_raise(mocker):
    def _raise(_):
        raise pika.exceptions.AMQPError

    (
        client,
        mock_pika,
        mock_connection,
        fake_connection_params,
    ) = _setup_health_check_test(mocker)
    mock_pika.exceptions.AMQPError = pika.exceptions.AMQPError
    mock_pika.BlockingConnection.side_effect = _raise
    assert not client.is_healthy


@pytest.mark.parametrize(
    "connection_states",
    [[True, False], [False, True], [True, True]],
)
def test_is_unhealthy(mocker, connection_states):
    (
        client,
        mock_pika,
        mock_connection,
        fake_connection_params,
    ) = _setup_health_check_test(mocker, *connection_states)
    assert not client.is_healthy

    mock_pika.BlockingConnection.assert_called_once_with(fake_connection_params)
    mock_connection.channel.assert_called_once()


def _setup_health_check_test(mocker, conn_closed=False, chan_closed=False):
    fake_connection_params = "connect_to_something"
    fake_queue = "queue"
    mock_pika = mocker.patch("common.rabbit.client.pika")
    client = RabbitMQClient("whatever", fake_queue)
    client._connection_parameters = fake_connection_params
    mock_connection = mock_pika.BlockingConnection.return_value
    mock_channel = mock_connection.channel.return_value
    mock_connection.is_closed = conn_closed
    mock_channel.is_closed = chan_closed
    return client, mock_pika, mock_connection, fake_connection_params
