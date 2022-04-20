from tests.assertions import assert_response
from web.endpoints import HealthStatus
from common.mongo.models.job import JobStatus
import bson
import pika
import pymongo
import pytest


def test_word_count_get(client, mocker):
    fake_job_id = "a_fake_job_id"
    expected_job = {"job_id": fake_job_id}
    _, mock_mongo, mock_job = _make_mocks(mocker)
    mock_job.fetch.return_value = expected_job

    response = client.get("word-count", json={"job_id": fake_job_id})

    mock_job.fetch.assert_called_once_with(mock_mongo, fake_job_id)

    def check_data(actual):
        assert actual.json["data"] == expected_job

    assert_response(response, 200, True, "Fetched Job", check_data)


def test_word_count_get_returns_bad_request_for_non_json_mime_type(client, mocker):
    _make_mocks(mocker)
    response = client.get("word-count", data={"some": "thing"})
    assert_response(response, 400, False, "application/json")


def test_word_count_get_returns_bad_request_for_missing_job_id(client, mocker):
    _make_mocks(mocker)
    response = client.get("word-count", json={})
    assert_response(response, 400, False, "job_id")


def test_word_count_get_returns_bad_request_for_unknown_job_id(client, mocker):
    _, mock_mongo, _ = _make_mocks(mocker)
    mock_mongo.exists.return_value = False
    response = client.get("word-count", json={"job_id": "wrong"})
    assert_response(response, 400, False, "job_id")


def test_word_count_get_returns_500_if_mongo_client_raises_pymongo_err(client, mocker):

    _, mongo_client, _ = _make_mocks(mocker)
    mongo_client.exists.side_effect = _raise_mongo_error
    response = client.get("word-count", json={"job_id": "fake_job_id"})
    assert_response(response, 500, False, "Oh dear")


def test_word_count_get_returns_500_if_mongo_client_raises_bson_err(client, mocker):
    _, mongo_client, _ = _make_mocks(mocker)
    mongo_client.exists.side_effect = _raise_bson_error
    response = client.get("word-count", json={"job_id": "fake_job_id"})
    assert_response(response, 500, False, "Oh dear")


def test_word_count_get_returns_500_if_job_model_raises_pymongo_err(client, mocker):
    _, _, mock_job = _make_mocks(mocker)
    mock_job.fetch.side_effect = _raise_mongo_error
    response = client.get("word-count", json={"job_id": "fake_job_id"})
    assert_response(response, 500, False, "Oh dear")


def test_word_count_get_returns_500_if_job_model_raises_bson_err(client, mocker):
    _, _, mock_job = _make_mocks(mocker)
    mock_job.fetch.side_effect = _raise_bson_error
    response = client.get("word-count", json={"job_id": "fake_job_id"})
    assert_response(response, 500, False, "Oh dear")


def test_word_count_post(client, mocker):
    fake_job_id, fake_url = "a_fake_job_id", "https://a.fake.url"
    expected_job = {
        "job_id": fake_job_id,
        "status": JobStatus.IN_PROGRESS.name,
        "url": fake_url,
    }
    mock_rabbit, mock_mongo, mock_job = _make_mocks(mocker)
    mock_job.create.return_value = expected_job

    response = client.post("word-count", json={"url": fake_url})

    mock_job.create.assert_called_once_with(mock_mongo, fake_url)
    mock_rabbit.publish.assert_called_once_with({"job_id": fake_job_id})

    def check_data(actual):
        assert actual.json["data"] == expected_job

    assert_response(response, 202, True, "Scheduled Job", check_data)


def test_word_count_post_returns_bad_request_for_non_json_mime_type(client, mocker):
    _make_mocks(mocker)
    response = client.post("word-count", data={"some": "thing"})
    assert_response(response, 400, False, "application/json")


def test_word_count_post_returns_400_if_url_not_present_in_request(client, mocker):
    _make_mocks(mocker)
    response = client.post("word-count", json={})
    assert_response(response, 400, False, "url")


@pytest.mark.parametrize(
    "malformed_url", ["", [], None, 1234, 56789.10, "nate", "nate.tech", False, {}]
)
def test_word_count_post_returns_bad_request_if_url_malformed(
    client, mocker, malformed_url
):
    _make_mocks(mocker)
    response = client.post("word-count", json={"url": malformed_url})
    assert_response(response, 400, False, "url")


def test_word_count_post_returns_500_if_rabbit_raises(client, mocker):
    mock_rabbit, _, _ = _make_mocks(mocker)
    mock_rabbit.publish.side_effect = _raise_amqp_error
    response = client.post("word-count", json={"url": "https://a.fake.url"})
    assert_response(response, 500, False, "Oh dear")


def test_word_count_post_returns_500_if_mongo_raises(client, mocker):
    _, _, mock_job = _make_mocks(mocker)
    mock_job.create.side_effect = _raise_mongo_error
    response = client.post("word-count", json={"url": "https://a.fake.url"})
    assert_response(response, 500, False, "Oh dear")


def test_word_count_post_returns_500_if_bson_raises(client, mocker):
    _, _, mock_job = _make_mocks(mocker)
    mock_job.create.side_effect = _raise_bson_error
    response = client.post("word-count", json={"url": "https://a.fake.url"})
    assert_response(response, 500, False, "Oh dear")


def test_health_pass(client, mocker):
    _ = _mock_property(mocker, "RabbitMQClient", "is_healthy", True)
    _ = _mock_property(mocker, "MongoDBClient", "is_healthy", True)
    response = client.get("health")
    assert_response(
        response,
        200,
        True,
        "Completed Health Check",
        _build_health_reponse_data_asserter(HealthStatus.PASS.name, "online"),
    )


@pytest.mark.parametrize(
    "rabbit_health,mongo_health", [[False, False], [True, False], [False, True]]
)
def test_health_fail(client, mocker, rabbit_health, mongo_health):
    _ = _mock_property(mocker, "RabbitMQClient", "is_healthy", rabbit_health)
    _ = _mock_property(mocker, "MongoDBClient", "is_healthy", mongo_health)
    response = client.get("health")
    assert_response(
        response,
        500,
        False,
        "Completed Health Check",
        _build_health_reponse_data_asserter(HealthStatus.FAIL.name, "offline"),
    )


def _build_health_reponse_data_asserter(status, info_content):
    def check_data(actual):
        assert actual.json["data"]["status"] == status
        assert str(info_content) in actual.json["data"]["info"]

    return check_data


def _make_mocks(mocker):
    targets = ["rabbit_client", "mongo_client", "Job"]
    return [mocker.patch(f"{ROOT_PATCH_PATH}.{t}") for t in targets]


def _mock_property(mocker, target, prop, value):
    return mocker.patch(
        f"{ROOT_PATCH_PATH}.{target}.{prop}",
        new_callable=mocker.PropertyMock,
        return_value=value,
    )


def _raise_mongo_error(_, __):
    raise pymongo.errors.PyMongoError


def _raise_bson_error(_, __):
    raise bson.errors.BSONError


def _raise_amqp_error(_):
    raise pika.exceptions.AMQPError


ROOT_PATCH_PATH = "web.endpoints"
