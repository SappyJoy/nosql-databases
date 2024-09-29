import random
from faker import Faker
from faker_airtravel import AirTravelProvider
from pymongo import MongoClient, InsertOne
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, SimpleStatement
from neo4j import GraphDatabase
from tqdm import tqdm
import json

fake = Faker()
fake.add_provider(AirTravelProvider)

# Настройки подключения
MONGO_URI = "mongodb://root:example@localhost:27017/"
CASSANDRA_CONTACT_POINTS = ['localhost']
CASSANDRA_KEYSPACE = 'airportflightmanagement'
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

# Количество записей
NUM_RECORDS = 2000000
BATCH_SIZE = 1000

# Функция генерации данных для MongoDB
def generate_mongo_data(num):
    for _ in range(num):
        passenger_id = fake.unique.uuid4()
        num_tickets = random.randint(1, 5)
        tickets = []
        for _ in range(num_tickets):
            ticket_number = fake.unique.uuid4()
            baggage_number = fake.unique.uuid4()
            ticket = {
                "TicketNumber": ticket_number,
                "Route": {
                    "Origin": fake.airport_iata(),
                    "Destination": fake.airport_iata()
                },
                "DepartureTime": fake.date_time_between(start_date='now', end_date='+1y'),
                "ArrivalTime": fake.date_time_between(start_date='+1h', end_date='+1y'),
                "Class": random.choice(["Economy", "Business", "First"]),
                "Price": round(random.uniform(100, 2000), 2),
                "TicketStatus": random.choice(["Confirmed", "Cancelled", "Pending"]),
                "Ratings": [random.randint(1, 5) for _ in range(random.randint(1, 5))],
                "Baggage": {
                    "BaggageNumber": baggage_number,
                    "BaggageType": random.choice(["Suitcase", "Backpack", "Carry-on"]),
                    "Weight": round(random.uniform(5, 50), 1),
                    "BaggageStatus": random.choice(["Checked", "Hand"]),
                    "Location": fake.airport_iata()
                }
            }
            tickets.append(ticket)
        passenger = {
            "PassengerID": passenger_id,
            "LastName": fake.last_name(),
            "FirstName": fake.first_name(),
            "MiddleName": fake.first_name(),
            "DateOfBirth": fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat(),
            "ContactInfo": {
                "Email": fake.email(),
                "Phone": fake.phone_number(),
                "Address": fake.address().replace("\n", ", ")
            },
            "IsTransit": random.choice([True, False]),
            "SpecialRequirements": random.choices(
                ["Mеждународный паспорт", "Место у прохода", "Питание для диабетиков", "Служебный живот", "Дополнительное место"], 
                k=random.randint(0,3)
            ),
            "Tickets": tickets
        }
        yield InsertOne(passenger)

# Функция вставки данных в MongoDB
def insert_into_mongodb():
    client = MongoClient(MONGO_URI)
    db = client['AirportFlightManagement']
    passengers_collection = db['Passengers']
    
    batch_size = 1000
    operations = []
    
    print("Начало вставки данных в MongoDB...")
    for _ in tqdm(range(0, NUM_RECORDS, batch_size)):
        for op in generate_mongo_data(batch_size):
            operations.append(op)
        if operations:
            passengers_collection.bulk_write(operations)
            operations = []
    print("Вставка данных в MongoDB завершена.")

# Функция генерации данных для Cassandra
def generate_cassandra_data(num):
    airlines = []
    aircrafts = []
    routes = []
    airports = set()
    flights = []

    # Предположим, что у нас есть 100 авиакомпаний, 500 самолётов и 1000 маршрутов
    NUM_AIRLINES = 100
    NUM_AIRCRAFTS = 500
    NUM_ROUTES = 1000

    # Генерация авиакомпаний
    for i in range(NUM_AIRLINES):
        airline_id = f"AL{i+1:04d}"
        airlines.append((
            airline_id,
            fake.company(),
            fake.country(),
            fake.email()
        ))

    # Генерация самолётов
    for i in range(NUM_AIRCRAFTS):
        aircraft_id = f"AC{i+1:05d}"
        aircrafts.append((
            aircraft_id,
            fake.word().upper(),
            fake.company(),
            random.randint(1990, 2023),
            random.randint(100, 300),
            json.dumps({"Engine": "Jet", "Range": random.randint(5000, 15000)})
        ))

    # Генерация маршрутов
    for i in range(NUM_ROUTES):
        route_id = f"R{i+1:05d}"
        origin = fake.airport_iata()
        destination = fake.airport_iata()
        distance = round(random.uniform(500, 15000), 1)
        travel_time = random.randint(60, 720)  # В минутах
        routes.append((
            route_id,
            origin,
            destination,
            distance,
            travel_time
        ))
        airports.add(origin)
        airports.add(destination)

    # Генерация аэропортов
    airports = list(airports)
    airports_data = []
    for code in airports:
        airports_data.append((
            code,
            fake.city(),
            fake.city(),
            fake.country(),
            fake.email()
        ))

    # Генерация рейсов
    for i in range(num):
        flight_number = f"FL{i+1:07d}"
        scheduled_departure = fake.date_time_between(start_date='now', end_date='+1y')
        scheduled_arrival = fake.date_time_between(start_date='+1h', end_date='+1y')
        actual_departure = scheduled_departure + fake.time_delta()
        actual_arrival = scheduled_arrival + fake.time_delta()
        flight_status = random.choice(["On Time", "Delayed", "Cancelled"])
        airline_id = random.choice(airlines)[0]
        aircraft_id = random.choice(aircrafts)[0]
        route_id = random.choice(routes)[0]
        flights.append((
            flight_number,
            scheduled_departure,
            scheduled_arrival,
            actual_departure,
            actual_arrival,
            flight_status,
            airline_id,
            aircraft_id,
            route_id
        ))

    return airlines, aircrafts, routes, airports_data, flights

# Функция вставки данных в Cassandra
def insert_into_cassandra():
    cluster = Cluster(CASSANDRA_CONTACT_POINTS)
    session = cluster.connect()
    
    # Создание Keyspace (если еще не создан)
    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS airportflightmanagement
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 3};
    """)
    
    session.set_keyspace(CASSANDRA_KEYSPACE)
    
    # Создание таблиц (если еще не созданы)
    session.execute("""
    CREATE TABLE IF NOT EXISTS Airlines (
        AirlineID text PRIMARY KEY,
        Name text,
        Country text,
        ContactInfo text
    );
    """)
    
    session.execute("""
    CREATE TABLE IF NOT EXISTS Aircrafts (
        AircraftID text PRIMARY KEY,
        Model text,
        Manufacturer text,
        YearOfManufacture int,
        Capacity int,
        Specifications text
    );
    """)
    
    session.execute("""
    CREATE TABLE IF NOT EXISTS Routes (
        RouteID text PRIMARY KEY,
        Origin text,
        Destination text,
        Distance double,
        TravelTime int
    );
    """)
    
    session.execute("""
    CREATE TABLE IF NOT EXISTS Airports (
        AirportCode text PRIMARY KEY,
        Name text,
        City text,
        Country text,
        ContactInfo text
    );
    """)
    
    session.execute("""
    CREATE TABLE IF NOT EXISTS Flights (
        FlightNumber text PRIMARY KEY,
        ScheduledDepartureTime timestamp,
        ScheduledArrivalTime timestamp,
        ActualDepartureTime timestamp,
        ActualArrivalTime timestamp,
        FlightStatus text,
        AirlineID text,
        AircraftID text,
        RouteID text
    );
    """)
    
    # Генерация и вставка данных
    airlines, aircrafts, routes, airports_data, flights = generate_cassandra_data(NUM_RECORDS // 1000)

    # Вставка авиакомпаний
    print("Вставка данных в таблицу Airlines...")
    insert_airlines = """
        INSERT INTO Airlines (AirlineID, Name, Country, ContactInfo)
        VALUES (?, ?, ?, ?)
    """
    prepared_insert_airlines = session.prepare(insert_airlines)
    batch_size = 100
    for i in tqdm(range(0, len(airlines), batch_size), desc="Airlines"):
        batch = BatchStatement()
        for airline in airlines[i:i+batch_size]:
            batch.add(prepared_insert_airlines, airline)
        session.execute(batch)

    # Вставка самолётов
    print("Вставка данных в таблицу Aircrafts...")
    insert_aircrafts = """
        INSERT INTO Aircrafts (AircraftID, Model, Manufacturer, YearOfManufacture, Capacity, Specifications)
        VALUES (?, ?, ?, ?, ?, ?)
    """
    prepared_insert_aircrafts = session.prepare(insert_aircrafts)
    for i in tqdm(range(0, len(aircrafts), batch_size), desc="Aircrafts"):
        batch = BatchStatement()
        for aircraft in aircrafts[i:i+batch_size]:
            batch.add(prepared_insert_aircrafts, aircraft)
        session.execute(batch)

    # Вставка маршрутов
    print("Вставка данных в таблицу Routes...")
    insert_routes = """
        INSERT INTO Routes (RouteID, Origin, Destination, Distance, TravelTime)
        VALUES (?, ?, ?, ?, ?)
    """
    prepared_insert_routes = session.prepare(insert_routes)
    for i in tqdm(range(0, len(routes), batch_size), desc="Routes"):
        batch = BatchStatement()
        for route in routes[i:i+batch_size]:
            batch.add(prepared_insert_routes, route )
        session.execute(batch)

    # Вставка аэропортов
    print("Вставка данных в таблицу Airports...")
    insert_airports = """
        INSERT INTO Airports (AirportCode, Name, City, Country, ContactInfo)
        VALUES (?, ?, ?, ?, ?)
    """
    prepared_insert_airports = session.prepare(insert_airports)
    for i in tqdm(range(0, len(airports_data), batch_size), desc="Airports"):
        batch = BatchStatement()
        for airport in airports_data[i:i+batch_size]:
            batch.add(prepared_insert_airports, airport)
        session.execute(batch)

    # Вставка рейсов
    print("Вставка данных в таблицу Flights...")
    insert_flights = """
        INSERT INTO Flights (
            FlightNumber,
            ScheduledDepartureTime,
            ScheduledArrivalTime,
            ActualDepartureTime,
            ActualArrivalTime,
            FlightStatus,
            AirlineID,
            AircraftID,
            RouteID
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    prepared_insert_flights = session.prepare(insert_flights)
    for i in tqdm(range(0, len(flights), batch_size), desc="Flights"):
        batch = BatchStatement()
        for flight in flights[i:i+batch_size]:
            batch.add(prepared_insert_flights, flight)
        session.execute(batch)

    # Закрытие соединения
    session.shutdown()
    cluster.shutdown()
    print("Вставка данных в Cassandra завершена.")

# Функция генерации данных для Neo4j
def generate_neo4j_data(num):
    # Для упрощения предположим, что некоторые данные уже существуют в MongoDB и Cassandra
    # Здесь мы сосредоточимся на создании связей между сущностями
    
    # В реальном проекте необходимо получить идентификаторы существующих сущностей из MongoDB и Cassandra
    # Для примера будем генерировать случайные связи
    for _ in range(num):
        passenger_id = fake.unique.uuid4()
        flight_number = f"FL{random.randint(1, 2000000):07d}"
        yield {
            "PassengerID": passenger_id,
            "FlightNumber": flight_number
        }

def generate_neo4j_relationships(batch_size):
    relationships = []
    for _ in range(batch_size):
        passenger_id = fake.unique.uuid4()
        flight_number = f"FL{random.randint(1, NUM_RECORDS):07d}"
        relationships.append((passenger_id, flight_number))
    return relationships

# Функция вставки данных в Neo4j
def insert_neo4j_batch(driver, relationships):
    with driver.session() as session:
        # Создание индексов
        session.run("CREATE INDEX IF NOT EXISTS FOR (p:Passenger) ON (p.PassengerID);")
        session.run("CREATE INDEX IF NOT EXISTS FOR (f:Flight) ON (f.FlightNumber);")
        tx = session.begin_transaction()
        for passenger_id, flight_number in relationships:
            tx.run("""
            MERGE (p:Passenger {PassengerID: $passenger_id})
            MERGE (f:Flight {FlightNumber: $flight_number})
            MERGE (p)-[:REGISTERED_ON]->(f)
            """, passenger_id=passenger_id, flight_number=flight_number)
        tx.commit()


# Функция вставки данных в Neo4j
# def insert_into_neo4j():
#     driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
#     session = driver.session()
#     
#     # Создание индексов
#     session.run("CREATE INDEX IF NOT EXISTS FOR (p:Passenger) ON (p.PassengerID);")
#     session.run("CREATE INDEX IF NOT EXISTS FOR (f:Flight) ON (f.FlightNumber);")
#     
#     print("Начало вставки данных в Neo4j...")
#     relationships = generate_neo4j_data(NUM_RECORDS)
#     for rel in tqdm(relationships, total=NUM_RECORDS):
#         passenger_id = rel["PassengerID"]
#         flight_number = rel["FlightNumber"]
#         session.run("""
#         MERGE (p:Passenger {PassengerID: $passenger_id})
#         MERGE (f:Flight {FlightNumber: $flight_number})
#         MERGE (p)-[:REGISTERED_ON]->(f)
#         """, passenger_id=passenger_id, flight_number=flight_number)
#     print("Вставка данных в Neo4j завершена.")
#     
#     session.close()
#     driver.close()

# Основная функция
def main():
    # Вставка в MongoDB
    insert_into_mongodb()
    
    # Вставка в Cassandra
    insert_into_cassandra()
    
    # Вставка в Neo4j
    # insert_into_neo4j()
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    total_batches = NUM_RECORDS // BATCH_SIZE
    for _ in tqdm(range(total_batches), desc="Вставка данных в Neo4j"):
        relationships = generate_neo4j_relationships(BATCH_SIZE)
        insert_neo4j_batch(driver, relationships)
    
    driver.close()
    print("Вставка данных в Neo4j завершена.")


if __name__ == "__main__":
    main()

