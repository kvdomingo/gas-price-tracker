from unittest.mock import MagicMock, patch

import pytest

from ingestion.robots import is_path_allowed


class TestRobotsChecker:
    def test_allowed_path_returns_true(self):
        robots_content = "User-agent: *\nAllow: /"
        mock_response = MagicMock()
        mock_response.text = robots_content

        with patch("ingestion.robots.polite_get", return_value=mock_response):
            assert (
                is_path_allowed("https://doe.gov.ph", "/articles/group/liquid-fuels")
                is True
            )

    def test_disallowed_path_returns_false(self):
        robots_content = "User-agent: *\nDisallow: /articles/"
        mock_response = MagicMock()
        mock_response.text = robots_content

        with patch("ingestion.robots.polite_get", return_value=mock_response):
            assert (
                is_path_allowed("https://doe.gov.ph", "/articles/group/liquid-fuels")
                is False
            )

    def test_network_error_defaults_to_allowed(self):
        with patch("ingestion.robots.polite_get", side_effect=Exception("timeout")):
            assert (
                is_path_allowed("https://doe.gov.ph", "/articles/group/liquid-fuels")
                is True
            )


class TestPoliteHTTP:
    def test_retries_on_failure(self):
        from ingestion.http_client import polite_get

        call_count = 0

        def failing_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("network error")
            mock = MagicMock()
            mock.raise_for_status = MagicMock()
            return mock

        with (
            patch("ingestion.http_client._get_session") as mock_session,
            patch("time.sleep"),
        ):
            mock_session.return_value.get = failing_get
            polite_get("https://example.com", delay=0, max_retries=3)
            assert call_count == 3

    def test_raises_after_max_retries(self):
        from ingestion.http_client import polite_get

        with (
            patch("ingestion.http_client._get_session") as mock_session,
            patch("time.sleep"),
            pytest.raises(Exception),
        ):
            mock_session.return_value.get = MagicMock(
                side_effect=Exception("network error")
            )
            polite_get("https://example.com", delay=0, max_retries=2)
