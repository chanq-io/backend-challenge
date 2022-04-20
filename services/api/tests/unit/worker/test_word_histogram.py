from worker.word_histogram import build


def test_build_with_empty_string():
    assert build("") == {}


def test_build_with_alphabetical_string():
    assert build("hello nate nate") == {"nate": 2, "hello": 1}


def test_build_with_alphanumerical_string():
    assert build("hello nate n4t3") == {"nate": 1, "n4t3": 1, "hello": 1}


def test_build_with_punctuation():
    assert build("hello, nate!") == {"hello": 1, "nate": 1}
