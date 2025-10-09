import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.storage.models import Base

TEST_DATABASE_URL = "postgresql://lipservice:lipservice@localhost:5433/lipservice_test"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    test_engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
