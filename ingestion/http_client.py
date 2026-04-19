import random
import time

import curl_cffi.requests as requests

_DEFAULT_DELAY_SECONDS = 1.0
_DEFAULT_MAX_RETRIES = 3
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session(impersonate="chrome")
    return _session


def polite_get(
    url: str,
    delay: float = _DEFAULT_DELAY_SECONDS,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> requests.Response:
    time.sleep(delay)
    session = _get_session()
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except Exception:
            if attempt == max_retries:
                raise
            backoff = (2**attempt) + random.uniform(0, 1)
            time.sleep(backoff)
            continue
    raise RuntimeError("unreachable")


def polite_download(
    url: str,
    dest_path: str,
    delay: float = _DEFAULT_DELAY_SECONDS,
    max_retries: int = _DEFAULT_MAX_RETRIES,
) -> None:
    time.sleep(delay)
    session = _get_session()
    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, timeout=60)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return
        except Exception:
            if attempt == max_retries:
                raise
            backoff = (2**attempt) + random.uniform(0, 1)
            time.sleep(backoff)
