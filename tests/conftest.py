import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.modelos import Base
from app.config import settings


@pytest.fixture(scope='module')
def db_engine():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope='function')
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
