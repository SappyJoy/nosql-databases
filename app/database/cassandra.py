from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import SimpleStatement
from cassandra import ReadTimeout, OperationTimedOut

import os

# Настройки подключения
CASSANDRA_CONTACT_POINTS = os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra1,cassandra2,cassandra3").split(',')
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "airportflightmanagement")
CASSANDRA_USERNAME = os.getenv("CASSANDRA_USERNAME", "cassandra")
CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD", "cassandra_password")

auth_provider = PlainTextAuthProvider(username=CASSANDRA_USERNAME, password=CASSANDRA_PASSWORD)
cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS, port=CASSANDRA_PORT, auth_provider=auth_provider)
cassandra_session = cluster.connect()

# Проверка подключения
try:
    cassandra_session.execute("SELECT now() FROM system.local")
    print("Подключение к Cassandra успешно.")
except Exception as e:
    print(f"Не удалось подключиться к Cassandra: {e}")
    # Здесь можно добавить логику для повторной попытки подключения

# Установите ключspace
cassandra_session.set_keyspace(CASSANDRA_KEYSPACE)
