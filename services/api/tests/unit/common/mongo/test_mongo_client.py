from bson.objectid import ObjectId as OID
from common.mongo.client import MongoDBClient
import pymongo


def test_construction(mocker):
    fake_host, fake_db = "host", "db"
    fake_db_instance = f"hello {fake_db}"
    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_mongo_client.return_value.__getitem__.return_value = fake_db_instance

    client = MongoDBClient(fake_host, fake_db)

    mock_mongo_client.assert_called_once_with(fake_host, 27017)
    mock_mongo_client.return_value.__getitem__.assert_called_once_with(fake_db)
    assert client.db == fake_db_instance


def test_create(mocker):
    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_db_instance = mocker.MagicMock()
    fake_collection, fake_document = "collection", "doc"
    mock_mongo_client.return_value.__getitem__.return_value = mock_db_instance
    client = MongoDBClient("host", "db")
    expected = "something"
    mock_db_instance.__getitem__.return_value.insert_one.return_value = expected

    actual = client.create(fake_collection, fake_document)

    mock_db_instance.__getitem__.assert_called_once_with(fake_collection)
    mock_db_instance.__getitem__.return_value.insert_one.assert_called_once_with(
        fake_document
    )
    assert expected == actual


def test_update(mocker):
    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_db_instance = mocker.MagicMock()
    fake_collection, fake_id = "collection", "625f4e3229942e20c16ca336"
    fake_updates = "update please"
    mock_mongo_client.return_value.__getitem__.return_value = mock_db_instance
    client = MongoDBClient("host", "db")
    expected = "something"
    mock_db_instance.__getitem__.return_value.update_one.return_value = expected

    actual = client.update(fake_collection, fake_id, fake_updates)

    mock_db_instance.__getitem__.assert_called_once_with(fake_collection)
    mock_db_instance.__getitem__.return_value.update_one.assert_called_once_with(
        {"_id": OID(fake_id)}, {"$set": fake_updates}
    )
    assert expected == actual


def test_retrieve(mocker):
    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_db_instance = mocker.MagicMock()
    fake_collection, fake_id = "collection", "625f4e3229942e20c16ca336"
    mock_mongo_client.return_value.__getitem__.return_value = mock_db_instance
    client = MongoDBClient("host", "db")
    expected = "something"
    mock_db_instance.__getitem__.return_value.find_one.return_value = expected

    actual = client.retrieve(fake_collection, fake_id)

    mock_db_instance.__getitem__.assert_called_once_with(fake_collection)
    mock_db_instance.__getitem__.return_value.find_one.assert_called_once_with(
        OID(fake_id)
    )
    assert expected == actual


def test_exists(mocker):
    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_db_instance = mocker.MagicMock()
    fake_collection, fake_id = "collection", "625f4e3229942e20c16ca336"
    mock_mongo_client.return_value.__getitem__.return_value = mock_db_instance
    client = MongoDBClient("host", "db")
    expected = True
    mock_db_instance.__getitem__.return_value.count_documents.return_value = int(
        expected
    )

    actual = client.exists(fake_collection, fake_id)

    mock_db_instance.__getitem__.assert_called_once_with(fake_collection)
    mock_db_instance.__getitem__.return_value.count_documents.assert_called_once_with(
        {"_id": OID(fake_id)}, limit=1
    )
    assert expected == actual


def test_is_healthy(mocker):
    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_mongo_client.return_value.server_info.return_value = True
    client = MongoDBClient("host", "db")
    assert client.is_healthy


def test_is_unhealthy(mocker):
    def _raise():
        raise pymongo.errors.ServerSelectionTimeoutError

    mock_mongo_client = mocker.patch("common.mongo.client.MongoClient")
    mock_mongo_client.return_value.server_info.side_effect = _raise
    client = MongoDBClient("host", "db")
    assert not client.is_healthy
