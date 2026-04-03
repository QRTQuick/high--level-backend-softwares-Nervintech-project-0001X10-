from __future__ import annotations

from urllib.parse import urljoin, urlparse


def build_endpoint_url(backend_url: str, backend_path: str) -> str:
    clean_base = backend_url.strip()
    clean_path = backend_path.strip()
    return urljoin(clean_base.rstrip("/") + "/", clean_path.lstrip("/"))


def is_https(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme.lower() == "https"


def host_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()
