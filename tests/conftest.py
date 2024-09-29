import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.mongodb import passengers_collection
from app.database.cassandra import session as cassandra_session
from app.database.neo4j import driver as neo4j_driver
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase

@pytest.fixture(scope="session")
def client():
    """
    Фикстура для создания тестового клиента FastAPI.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="session")
def mongodb_test_db():
    """
    Фикстура для подключения к тестовой базе данных MongoDB.
    """
    test_db = MongoClient("mongodb://root:example@localhost:27017/")['AirportFlightManagementTest']
    # Очистка коллекции перед тестами
    test_db['Passengers'].delete_many({})
    yield test_db
    # Очистка после тестов
    test_db['Passengers'].delete_many({})

@pytest.fixture(scope="session")
def cassandra_test_session():
    """
    Фикстура для подключения к тестовой Cassandra сессии.
    """
    cluster = Cluster(['localhost'], port=9042)
    session = cluster.connect('airportflightmanagement')
    # Очистка таблиц перед тестами
    session.execute("TRUNCATE flights")
    # Повторите для других таблиц, если необходимо
    yield session
    # Очистка после тестов
    session.execute("TRUNCATE flights")
    session.shutdown()
    cluster.shutdown()

@pytest.fixture(scope="session")
def neo4j_test_driver():
    """
    Фикстура для подключения к тестовому Neo4j драйверу.
    """
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    # Очистка графа перед тестами
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    yield driver
    # Очистка после тестов
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    driver.close()

