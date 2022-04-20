from common.mongo.models import job as Job
from bson.objectid import ObjectId as OID


def test_create(mocker):
    mock_mongo = mocker.MagicMock()
    fake_id, fake_url = "allowed_to_buy_beer", "www.w.ww"
    expected = "something"
    mock_mongo.create.return_value.inserted_id = fake_id
    mock_fetch = _mock_fetch(mocker, expected)
    actual = Job.create(mock_mongo, fake_url)
    mock_mongo.create.assert_called_once_with(
        Job.COLLECTION, {"status": "IN_PROGRESS", "url": fake_url}
    )
    mock_fetch.assert_called_once_with(mock_mongo, fake_id)
    assert expected == actual


def test_complete(mocker):
    mock_mongo = mocker.MagicMock()
    fake_id, fake_word_count = "allowed_to_buy_beer", {"hello": 1}
    expected = "something"
    mock_fetch = _mock_fetch(mocker, expected)
    actual = Job.complete(mock_mongo, fake_id, fake_word_count)
    mock_mongo.update.assert_called_once_with(
        Job.COLLECTION, fake_id, {"status": "COMPLETE", "word_count": fake_word_count}
    )
    mock_fetch.assert_called_once_with(mock_mongo, fake_id)
    assert expected == actual


def test_fail(mocker):
    mock_mongo = mocker.MagicMock()
    fake_id, fake_error = "allowed_to_buy_beer", "denied"
    expected = "something"
    mock_fetch = _mock_fetch(mocker, expected)
    actual = Job.fail(mock_mongo, fake_id, fake_error)
    mock_mongo.update.assert_called_once_with(
        Job.COLLECTION, fake_id, {"status": "FAIL", "error": fake_error}
    )
    mock_fetch.assert_called_once_with(mock_mongo, fake_id)
    assert expected == actual


def test_fetch(mocker):
    mock_mongo = mocker.MagicMock()
    fake_id = "625f4e3229942e20c16ca336"
    expected = {"job_id": fake_id, "something": "else"}
    mock_mongo.retrieve.return_value = {"_id": OID(fake_id), "something": "else"}
    actual = Job.fetch(mock_mongo, fake_id)
    mock_mongo.retrieve.assert_called_once_with(Job.COLLECTION, fake_id)
    assert expected == actual


def _mock_fetch(mocker, expected):
    return mocker.patch("common.mongo.models.job.fetch", return_value=expected)
