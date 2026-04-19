import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="session")
def test_db_url() -> str:
    import os

    return os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/gas_price_tracker_test",
    )


@pytest.fixture(scope="session")
def db_engine(test_db_url: str):
    engine = create_engine(test_db_url)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def api_client(test_db_url: str, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    from api.main import app
    from api.database import get_db

    Session = sessionmaker(bind=create_engine(test_db_url))

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
