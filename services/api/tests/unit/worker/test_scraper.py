from worker.scraper import scrape_text
import pytest


def test_scrape_text_raises_for_non_200_status(mocker):
    mock_requests = _patch_requests(mocker, 505, "")
    with pytest.raises(RuntimeError):
        url = "https://im-gonna-raise.com"
        scrape_text(url)
        mock_requests.get.assert_called_once_with(url, allow_redirects=True)


def test_scrape_text_returns_joined_text(mocker):
    def _make_fake_html(title, h1, p, a, should_be_ignored):
        return f"""
            <html>
                <head><title>{title}</title><style>{should_be_ignored}</style></head>
                <body>
                    <h1>{h1}</h1><p>{p}</p><a href="https://some.url">{a}</a>
                    <script>{should_be_ignored}</script>
                    <template>{should_be_ignored}></template>
                </body>
            </html>"""

    url, title, h1, p, a = "https://will-parse.co.uk", "a", "b", "c", 'd "e"?'
    expected = " ".join([title, h1, p, a])
    mock_requests = _patch_requests(
        mocker, 200, _make_fake_html(title, h1, p, a, "should be ignored")
    )
    actual = scrape_text(url)
    mock_requests.get.assert_called_once_with(url, allow_redirects=True)
    assert expected == actual


def _patch_requests(mocker, status_code, content):
    mock_requests = mocker.patch("worker.scraper.requests")
    mock_requests.get.return_value = mocker.MagicMock(
        status_code=status_code, content=content
    )
    return mock_requests
