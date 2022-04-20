import requests
import json
import time


def test_health():
    def check_data(body):
        assert body["data"]["info"] == "All services are online"
        assert body["data"]["status"] == "PASS"

    assert_e2e_response(
        get("http://web:5000/health"), 200, True, "Health Check", check_data
    )


def test_word_count_complete():
    def check_get_complete_data(body):
        assert "word_count" in body["data"]
        assert body["data"]["status"] == "COMPLETE"

    data = {"url": "https://nate.tech"}
    response = post("http://web:5000/word-count", data)
    body = response.json()
    assert_e2e_response(response, 202, True, "Scheduled Job", check_post_data)

    data = {"job_id": body["data"]["job_id"]}
    response = get("http://web:5000/word-count", data=data)
    assert_e2e_response(response, 200, True, "Fetched Job", check_get_in_progress_data)

    time.sleep(2)

    data = {"job_id": body["data"]["job_id"]}
    response = get("http://web:5000/word-count", data=data)
    assert_e2e_response(response, 200, True, "Fetched Job", check_get_complete_data)


def test_word_count_fail():
    def check_get_fail_data(body):
        assert "word_count" not in body["data"]
        assert body["data"]["status"] == "FAIL"

    data = {"url": "https://www.unl1k3y.tob3aurl"}
    response = post("http://web:5000/word-count", data)
    body = response.json()
    assert_e2e_response(response, 202, True, "Scheduled Job", check_post_data)

    data = {"job_id": body["data"]["job_id"]}
    response = get("http://web:5000/word-count", data=data)
    assert_e2e_response(response, 200, True, "Fetched Job", check_get_in_progress_data)

    time.sleep(2)

    data = {"job_id": body["data"]["job_id"]}
    response = get("http://web:5000/word-count", data=data)
    assert_e2e_response(response, 200, True, "Fetched Job", check_get_fail_data)


def post(url, data={}):
    return requests.post(url, data=json.dumps(data), headers=JSON_HEADERS)


def get(url, data={}):
    return requests.get(url, data=json.dumps(data), headers=JSON_HEADERS)


def assert_e2e_response(response, status_code, success, message, data_assertion_cb):
    body = response.json()
    assert response.status_code == status_code
    assert body["success"] == success
    assert message in body["message"]
    data_assertion_cb(body)


def check_post_data(body):
    assert "job_id" in body["data"]
    assert body["data"]["status"] == "IN_PROGRESS"


def check_get_in_progress_data(body):
    assert "word_count" not in body["data"]
    assert body["data"]["status"] == "IN_PROGRESS"


JSON_HEADERS = {"Content-Type": "application/json"}
