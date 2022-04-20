from worker import consumer
import bson
import pytest
import pika
import pymongo


def test_consume_complete(mocker):
    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_scraper.scrape_text.return_value = FAKE_HTML
    mock_whist.build.return_value = FAKE_WORD_COUNT
    mock_job.fetch.return_value = {"job_id": FAKE_JOB_ID, "url": FAKE_URL}
    mock_job.complete.return_value = {}
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_job.fetch.assert_called_once_with(mock_mongo, FAKE_JOB_ID)
    mock_scraper.scrape_text.assert_called_once_with(FAKE_URL)
    mock_whist.build.assert_called_once_with(FAKE_HTML)
    mock_job.complete.assert_called_once_with(mock_mongo, FAKE_JOB_ID, FAKE_WORD_COUNT)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_job.fail.assert_not_called()
    mock_job.create.assert_not_called()


def test_consume_rabbit_error_raises(mocker):
    def _raise(_):
        raise pika.exceptions.AMQPError

    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_rabbit.consume.side_effect = _raise

    with pytest.raises(pika.exceptions.AMQPError):
        consumer.consume()


def test_consume_malformed_json_fails_silently(mocker):
    fake_body = "not valid json"
    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, fake_body)

    mock_job.fetch.assert_not_called()
    mock_scraper.scrape_text.assert_not_called()
    mock_job.fail.assert_not_called()
    mock_whist.build.assert_not_called()
    mock_job.complete.assert_not_called()
    mock_job.create.assert_not_called()
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)


def test_consume_missing_job_id_fails_silently(mocker):
    fake_body = "{}"
    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, fake_body)

    mock_job.fetch.assert_not_called()
    mock_scraper.scrape_text.assert_not_called()
    mock_job.fail.assert_not_called()
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_whist.build.assert_not_called()
    mock_job.complete.assert_not_called()
    mock_job.create.assert_not_called()


def test_consume_unknown_job_id_fails_silently(mocker):
    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_job.COLLECTION = "something"
    mock_mongo.exists.return_value = False
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_mongo.exists.assert_called_once_with(mock_job.COLLECTION, FAKE_JOB_ID)
    mock_job.fetch.assert_not_called()
    mock_scraper.scrape_text.assert_not_called()
    mock_job.fail.assert_not_called()
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_whist.build.assert_not_called()
    mock_job.complete.assert_not_called()
    mock_job.create.assert_not_called()


def test_consume_malformed_job_id_fails_silently(mocker):
    def _raise(_, __):
        raise bson.errors.BSONError

    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_mongo.exists.side_effect = _raise
    mock_job.COLLECTION = "something"
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_mongo.exists.assert_called_once_with(mock_job.COLLECTION, FAKE_JOB_ID)
    mock_job.fetch.assert_not_called()
    mock_scraper.scrape_text.assert_not_called()
    mock_job.fail.assert_not_called()
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_whist.build.assert_not_called()
    mock_job.complete.assert_not_called()
    mock_job.create.assert_not_called()


def test_consume_fail_mongo_error_on_complete(mocker):
    err_message = "oh no"
    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_scraper.scrape_text.return_value = FAKE_HTML
    mock_whist.build.return_value = FAKE_WORD_COUNT
    mock_job.complete.side_effect = _make_mongo_raiser(err_message)
    mock_job.fetch.return_value = {"job_id": FAKE_JOB_ID, "url": FAKE_URL}
    mock_job.fail.return_value = {}
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_job.fetch.assert_called_once_with(mock_mongo, FAKE_JOB_ID)
    mock_scraper.scrape_text.assert_called_once_with(FAKE_URL)
    mock_whist.build.assert_called_once_with(FAKE_HTML)
    mock_job.complete.assert_called_once_with(mock_mongo, FAKE_JOB_ID, FAKE_WORD_COUNT)
    mock_job.fail.assert_called_once_with(mock_mongo, FAKE_JOB_ID, err_message)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_job.create.assert_not_called()


def test_consume_fail_mongo_error_on_fetch(mocker):
    err_message = "oh no"

    def _raise(_, __):
        raise pymongo.errors.PyMongoError(err_message)

    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_job.fetch.side_effect = _raise
    mock_job.fail.return_value = {}
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_job.fetch.assert_called_once_with(mock_mongo, FAKE_JOB_ID)
    mock_job.fail.assert_called_once_with(mock_mongo, FAKE_JOB_ID, err_message)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_job.complete.assert_not_called()
    mock_whist.build.assert_not_called()
    mock_scraper.scrape_text.assert_not_called()
    mock_job.create.assert_not_called()


def test_consume_fail_mongo_error_on_fail(mocker):
    err_message = "oh no"

    def _raise(_, __):
        raise pymongo.errors.PyMongoError(err_message)

    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_job.fetch.side_effect = _raise
    mock_job.fail.side_effect = _make_mongo_raiser(err_message)
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_job.fetch.assert_called_once_with(mock_mongo, FAKE_JOB_ID)
    mock_job.fail.assert_called_once_with(mock_mongo, FAKE_JOB_ID, err_message)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_job.complete.assert_not_called()
    mock_whist.build.assert_not_called()
    mock_scraper.scrape_text.assert_not_called()
    mock_job.create.assert_not_called()


def test_consume_fail_scraper_error(mocker):

    err_message = "oh no"

    def _raise(_):
        raise RuntimeError(err_message)

    mock_rabbit, mock_mongo, mock_job, mock_scraper, mock_whist = _make_mocks(mocker)
    mock_scraper.scrape_text.side_effect = _raise
    mock_job.fetch.return_value = {"job_id": FAKE_JOB_ID, "url": FAKE_URL}
    mock_job.fail.return_value = {}
    mock_channel = mocker.MagicMock()
    mock_method = mocker.MagicMock()
    mock_method.delivery_tag = FAKE_DELIVERY_TAG

    consumer.consume()

    mock_rabbit.consume.assert_called_once()
    callback = mock_rabbit.consume.call_args.args[0]
    callback(mock_channel, mock_method, None, FAKE_BODY)

    mock_job.fetch.assert_called_once_with(mock_mongo, FAKE_JOB_ID)
    mock_scraper.scrape_text.assert_called_once_with(FAKE_URL)
    mock_job.fail.assert_called_once_with(mock_mongo, FAKE_JOB_ID, err_message)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=FAKE_DELIVERY_TAG)
    mock_whist.build.assert_not_called()
    mock_job.complete.assert_not_called()
    mock_job.create.assert_not_called()


def _patch(mocker, key):
    return mocker.patch(f"worker.consumer.{key}")


def _make_mongo_raiser(error_message):
    def _raise(_, __, ___):
        raise pymongo.errors.PyMongoError(error_message)

    return _raise


def _make_mocks(mocker):
    return [
        _patch(mocker, k)
        for k in ["rabbit_client", "mongo_client", "Job", "scraper", "word_histogram"]
    ]


FAKE_HTML = "<tag></tag>"
FAKE_WORD_COUNT = {"hello": 1}
FAKE_JOB_ID = "something"
FAKE_URL = "https://nate.tech"
FAKE_DELIVERY_TAG = "something"
FAKE_BODY = '{"job_id": "' + FAKE_JOB_ID + '"}'
