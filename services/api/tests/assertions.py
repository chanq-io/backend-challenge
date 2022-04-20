def assert_response(
    actual,
    exp_status_code,
    exp_success,
    exp_message_stub,
    data_assertion_cb=lambda _: None,
):
    assert actual.status_code == exp_status_code
    assert actual.json["success"] == exp_success
    assert exp_message_stub in actual.json["message"]
    data_assertion_cb(actual)
