from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import os
import itertools
import time

# Настройки подключения
NEO4J_URIS = os.getenv("NEO4J_URIS", "bolt://neo4j1:7687,bolt://neo4j2:7687,bolt://neo4j3:7687").split(',')
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def get_driver():
    for uri in NEO4J_URIS:
        try:
            driver = GraphDatabase.driver(uri, auth=(NEO4J_USER, NEO4J_PASSWORD))
            # Тестирование подключения
            with driver.session() as session:
                session.run("RETURN 1")
            print(f"Подключение к {uri} успешно.")
            return driver
        except ServiceUnavailable as e:
            print(f"Не удалось подключиться к {uri}: {e}")
    raise Exception("Не удалось подключиться ни к одному из узлов Neo4j.")

driver = get_driver()

def get_neo4j_session():
    return driver.session()

# Глобальная функция для закрытия драйвера при завершении работы приложения
def close_driver():
    driver.close()
