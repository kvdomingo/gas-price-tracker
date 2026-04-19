from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

from .http_client import polite_get

USER_AGENT = "gas-price-tracker/1.0"


def is_path_allowed(base_url: str, path: str) -> bool:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = polite_get(robots_url)
        rp = RobotFileParser()
        rp.parse(response.text.splitlines())
        full_url = urljoin(base_url, path)
        parsed = urlparse(full_url)
        return rp.can_fetch(USER_AGENT, parsed.path)
    except Exception:
        return True
