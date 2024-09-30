import json
import os
import random

from cassandra.cluster import Cluster
from cassandra.query import BatchStatement
from faker import Faker
from faker_airtravel import AirTravelProvider
from tqdm import tqdm

fake = Faker()
fake.add_provider(AirTravelProvider)

CASSANDRA_CONTACT_POINTS = os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra1")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "airportflightmanagement")
NUM_RECORDS = 2000000

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
    # cluster = Cluster(CASSANDRA_CONTACT_POINTS)
    # session = cluster.connect()
    contact_points = CASSANDRA_CONTACT_POINTS.split(',')
    cluster = Cluster(contact_points=contact_points, port=CASSANDRA_PORT)
    session = cluster.connect()
    
    # Создание Keyspace (если еще не создан)
    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS airportflightmanagement
    WITH replication = {'class': 'NetworkTopologyStrategy', 'DC1' : 3}
    AND durable_writes = true;
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


def main():
    insert_into_cassandra()


if __name__ == "__main__":
    main()


