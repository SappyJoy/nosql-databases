from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Настройки подключения
CASSANDRA_CONTACT_POINTS = ['localhost']
CASSANDRA_PORT = 9042
CASSANDRA_KEYSPACE = 'airportflightmanagement'

cassandra_cluster = Cluster(CASSANDRA_CONTACT_POINTS, port=CASSANDRA_PORT)
cassandra_session = cassandra_cluster.connect(CASSANDRA_KEYSPACE)

# Пример использования:
# session.execute("SELECT * FROM Flights LIMIT 10")

