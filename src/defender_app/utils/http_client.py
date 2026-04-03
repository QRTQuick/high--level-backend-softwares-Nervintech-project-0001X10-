from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class HTTPResult:
    status_code: int | None
    headers: dict[str, str]
    body: str
    response_ms: float | None
    error: str | None = None


def request_url(
    url: str,
    method: str = "GET",
    timeout: float = 5.0,
    headers: dict[str, str] | None = None,
    query: dict[str, str] | None = None,
) -> HTTPResult:
    method = method.upper().strip()
    headers = headers or {}

    if query:
        suffix = urlencode(query)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{suffix}"

    req = Request(url=url, method=method, headers=headers)
    start = perf_counter()

    try:
        with urlopen(req, timeout=timeout) as response:
            body_bytes = response.read(8192)
            elapsed = (perf_counter() - start) * 1000
            return HTTPResult(
                status_code=response.status,
                headers={k.lower(): v for k, v in response.getheaders()},
                body=body_bytes.decode("utf-8", errors="replace"),
                response_ms=elapsed,
            )
    except HTTPError as err:
        elapsed = (perf_counter() - start) * 1000
        body = err.read(8192).decode("utf-8", errors="replace") if err.fp else ""
        return HTTPResult(
            status_code=err.code,
            headers={k.lower(): v for k, v in err.headers.items()},
            body=body,
            response_ms=elapsed,
            error=f"HTTPError: {err}",
        )
    except URLError as err:
        elapsed = (perf_counter() - start) * 1000
        return HTTPResult(
            status_code=None,
            headers={},
            body="",
            response_ms=elapsed,
            error=f"URLError: {err}",
        )
    except TimeoutError as err:
        elapsed = (perf_counter() - start) * 1000
        return HTTPResult(
            status_code=None,
            headers={},
            body="",
            response_ms=elapsed,
            error=f"TimeoutError: {err}",
        )
