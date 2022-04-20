from web.endpoints import server
import pytest


@pytest.fixture()
def app():
    server.config.update({"TESTING": True})
    yield server


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
