from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .http_client import request_url


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() != "a":
            return
        attr_map = dict(attrs)
        href = attr_map.get("href")
        if href:
            self.links.append(href)


def discover_frontend_routes(frontend_url: str, timeout: float = 5.0) -> list[str]:
    response = request_url(frontend_url, method="GET", timeout=timeout)
    if response.status_code is None or response.status_code >= 400:
        return []

    parser = _AnchorParser()
    parser.feed(response.body)

    base_host = urlparse(frontend_url).netloc
    routes: set[str] = set()

    for link in parser.links:
        absolute = urljoin(frontend_url, link)
        parsed = urlparse(absolute)
        if parsed.netloc and parsed.netloc != base_host:
            continue
        if not parsed.path:
            continue
        routes.add(parsed.path)

    if "/" not in routes:
        routes.add("/")

    return sorted(routes)
