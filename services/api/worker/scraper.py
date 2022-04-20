import requests

from bs4 import BeautifulSoup


def scrape_text(url: str) -> str:
    response = requests.get(url, allow_redirects=True)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        return " ".join(t for t in soup.stripped_strings)
    raise RuntimeError(f"Unable to scrape {url}")
