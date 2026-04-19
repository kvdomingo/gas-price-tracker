"""API endpoint tests using the test database."""

from unittest.mock import MagicMock, patch


class TestHealthEndpoint:
    def test_health_ok_when_db_reachable(self, api_client):
        with patch("api.main.check_db_connection", return_value=True):
            response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_degraded_when_db_unreachable(self, api_client):
        with patch("api.main.check_db_connection", return_value=False):
            response = api_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"


class TestPricesLatestEndpoint:
    def test_returns_404_when_no_records(self, api_client):
        with patch("storage.queries.get_latest_prices_by_region", return_value=[]):
            response = api_client.get("/prices/latest?region=130000000")
        assert response.status_code == 404

    def test_returns_prices_for_region(self, api_client):
        from datetime import date, datetime

        mock_record = MagicMock()
        mock_record.id = "abc123"
        mock_record.effective_date = date(2024, 1, 5)
        mock_record.psgc_code = "137502000"
        mock_record.fuel_type = "diesel"
        mock_record.price_php_per_liter = 62.5
        mock_record.raw_location = "Makati City"
        mock_record.ingested_at = datetime(2024, 1, 6)

        with patch(
            "storage.queries.get_latest_prices_by_region", return_value=[mock_record]
        ):
            response = api_client.get("/prices/latest?region=130000000")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["fuel_type"] == "diesel"


class TestPricesHistoryEndpoint:
    def test_returns_empty_list_when_no_records(self, api_client):
        with patch("storage.queries.get_price_history", return_value=[]):
            response = api_client.get("/prices?region=130000000")
        assert response.status_code == 200
        assert response.json() == []

    def test_validates_date_format(self, api_client):
        response = api_client.get("/prices?region=130000000&from=not-a-date")
        assert response.status_code == 422


class TestDocsEndpoint:
    def test_scalar_docs_accessible(self, api_client):
        response = api_client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json_accessible(self, api_client):
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        assert "openapi" in response.json()
