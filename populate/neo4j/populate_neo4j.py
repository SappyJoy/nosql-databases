import os
import random
from faker import Faker
from faker_airtravel import AirTravelProvider
from neo4j import GraphDatabase, basic_auth
from tqdm import tqdm

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NUM_RECORDS = int(os.getenv("NUM_RECORDS", "2000000"))
BATCH_SIZE = 1000

fake = Faker()
fake.add_provider(AirTravelProvider)

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

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD))

    total_batches = NUM_RECORDS // BATCH_SIZE
    for _ in tqdm(range(total_batches), desc="Вставка данных в Neo4j"):
        relationships = generate_neo4j_relationships(BATCH_SIZE)
        insert_neo4j_batch(driver, relationships)

    driver.close()
    print("Вставка данных в Neo4j завершена.")


if __name__ == "__main__":
    main()



# import os
# from neo4j import GraphDatabase, basic_auth
# from faker import Faker
# import random
# from tqdm import tqdm
# import uuid
#
# fake = Faker()
#
# # Получение переменных окружения
# NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j1:7687")
# NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
# NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
# NUM_RECORDS = int(os.getenv("NUM_RECORDS", "2000000"))
#
# # Параметры генерации
# NUM_AIRLINES = 10
# NUM_AIRCRAFT = 100
# NUM_AIRPORTS = 50
# NUM_ROUTES = 1000
# NUM_FLIGHTS = 10000
#
# class Neo4jPopulator:
#     def __init__(self, uri, user, password):
#         self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
#     
#     def close(self):
#         self.driver.close()
#     
#     def create_constraints(self):
#         with self.driver.session() as session:
#             # Создание уникальных ограничений
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (p:Passenger) ASSERT p.PassengerID IS UNIQUE")
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (f:Flight) ASSERT f.FlightID IS UNIQUE")
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (f:Flight) ASSERT f.FlightNumber IS UNIQUE")
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (r:Route) ASSERT r.RouteID IS UNIQUE")
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (a:Airport) ASSERT a.AirportCode IS UNIQUE")
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (ac:Aircraft) ASSERT ac.AircraftID IS UNIQUE")
#             session.run("CREATE CONSTRAINT IF NOT EXISTS ON (al:Airline) ASSERT al.AirlineID IS UNIQUE")
#     
#     def populate_static_data(self):
#         with self.driver.session() as session:
#             # Генерация Airlines
#             airlines = []
#             for _ in range(NUM_AIRLINES):
#                 airline_id = str(uuid.uuid4())
#                 name = fake.company()
#                 iata_code = fake.unique.lexify(text='??').upper()
#                 airlines.append((airline_id, name, iata_code))
#             
#             # Вставка Airlines
#             session.run(
#                 """
#                 UNWIND $airlines AS al
#                 MERGE (a:Airline {AirlineID: al.airline_id})
#                 SET a.Name = al.name,
#                     a.IATA_Code = al.iata_code
#                 """,
#                 airlines=[{"airline_id": a[0], "name": a[1], "iata_code": a[2]} for a in airlines]
#             )
#             
#             # Генерация Aircraft
#             aircrafts = []
#             for _ in range(NUM_AIRCRAFT):
#                 aircraft_id = str(uuid.uuid4())
#                 model = fake.bothify(text='???-####')
#                 capacity = random.randint(100, 500)
#                 aircrafts.append((aircraft_id, model, capacity))
#             
#             # Вставка Aircraft
#             session.run(
#                 """
#                 UNWIND $aircrafts AS ac
#                 MERGE (a:Aircraft {AircraftID: ac.aircraft_id})
#                 SET a.Model = ac.model,
#                     a.Capacity = ac.capacity
#                 """,
#                 aircrafts=[{"aircraft_id": a[0], "model": a[1], "capacity": a[2]} for a in aircrafts]
#             )
#             
#             # Генерация Airports
#             airports = []
#             for _ in range(NUM_AIRPORTS):
#                 airport_code = fake.unique.lexify(text='???').upper()
#                 name = f"{fake.city()} International Airport"
#                 city = fake.city()
#                 country = fake.country()
#                 airports.append((airport_code, name, city, country))
#             
#             # Вставка Airports
#             session.run(
#                 """
#                 UNWIND $airports AS ap
#                 MERGE (a:Airport {AirportCode: ap.airport_code})
#                 SET a.Name = ap.name,
#                     a.City = ap.city,
#                     a.Country = ap.country
#                 """,
#                 airports=[{"airport_code": a[0], "name": a[1], "city": a[2], "country": a[3]} for a in airports]
#             )
#             
#             # Генерация Routes
#             routes = []
#             for _ in range(NUM_ROUTES):
#                 route_id = str(uuid.uuid4())
#                 origin = random.choice(airports)[0]
#                 destination = random.choice([ap for ap in airports if ap[0] != origin])[0]
#                 routes.append((route_id, origin, destination))
#             
#             # Вставка Routes
#             session.run(
#                 """
#                 UNWIND $routes AS r
#                 MERGE (route:Route {RouteID: r.route_id})
#                 WITH route, r
#                 MATCH (origin:Airport {AirportCode: r.origin})
#                 MATCH (destination:Airport {AirportCode: r.destination})
#                 MERGE (route)-[:DEPARTS_FROM]->(origin)
#                 MERGE (route)-[:ARRIVES_AT]->(destination)
#                 """,
#                 routes=[{"route_id": r[0], "origin": r[1], "destination": r[2]} for r in routes]
#             )
#             
#             # Генерация Flights
#             flights = []
#             for _ in range(NUM_FLIGHTS):
#                 flight_id = str(uuid.uuid4())
#                 flight_number = fake.unique.bothify(text='??-#####').upper()
#                 departure_time = fake.date_time_between(start_date='now', end_date='+1y').isoformat()
#                 arrival_time = fake.date_time_between(start_date='+1h', end_date='+1y').isoformat()
#                 flight_class = random.choice(["Economy", "Business", "First"])
#                 price = round(random.uniform(100, 2000), 2)
#                 status = random.choice(["On Time", "Delayed", "Cancelled"])
#                 route = random.choice(routes)[0]
#                 aircraft = random.choice(aircrafts)[0]
#                 airline = random.choice(airlines)[0]
#                 flights.append((flight_id, flight_number, departure_time, arrival_time, flight_class, price, status, route, aircraft, airline))
#             
#             # Вставка Flights
#             session.run(
#                 """
#                 UNWIND $flights AS f
#                 MERGE (fl:Flight {FlightID: f.flight_id})
#                 SET fl.FlightNumber = f.flight_number,
#                     fl.DepartureTime = datetime(f.departure_time),
#                     fl.ArrivalTime = datetime(f.arrival_time),
#                     fl.Class = f.flight_class,
#                     fl.Price = f.price,
#                     fl.Status = f.status
#                 WITH fl, f
#                 MATCH (r:Route {RouteID: f.route})
#                 MATCH (ac:Aircraft {AircraftID: f.aircraft})
#                 MATCH (al:Airline {AirlineID: f.airline})
#                 MERGE (fl)-[:HAS_ROUTE]->(r)
#                 MERGE (fl)-[:OPERATED_BY]->(ac)
#                 MERGE (fl)-[:AFFILIATED_WITH]->(al)
#                 """,
#                 flights=[{
#                     "flight_id": f[0],
#                     "flight_number": f[1],
#                     "departure_time": f[2],
#                     "arrival_time": f[3],
#                     "flight_class": f[4],
#                     "price": f[5],
#                     "status": f[6],
#                     "route": f[7],
#                     "aircraft": f[8],
#                     "airline": f[9]
#                 } for f in flights]
#             )
#     
#     def populate_passengers(self):
#         with self.driver.session() as session:
#             print("Начало вставки данных в Neo4j Passengers...")
#             batch_size = 1000
#             for _ in tqdm(range(0, NUM_RECORDS, batch_size)):
#                 passengers = []
#                 registrations = []
#                 for _ in range(batch_size):
#                     passenger_id = str(uuid.uuid4())
#                     last_name = fake.last_name()
#                     first_name = fake.first_name()
#                     middle_name = fake.first_name()
#                     date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
#                     email = fake.email()
#                     phone = fake.phone_number()
#                     address = fake.address().replace("\n", ", ")
#                     is_transit = random.choice([True, False])
#                     special_requirements = random.sample(
#                         ["Международный паспорт", "Место у прохода", "Питание для диабетиков", "Служебный живот", "Дополнительное место"],
#                         k=random.randint(0,3)
#                     )
#                     flight = random.randint(1, NUM_FLIGHTS)
#                     flight_number = f"FL-{flight:05d}"  # Assuming FlightNumbers were generated as 'FL-00001', etc.
#                     
#                     passengers.append({
#                         "PassengerID": passenger_id,
#                         "LastName": last_name,
#                         "FirstName": first_name,
#                         "MiddleName": middle_name,
#                         "DateOfBirth": date_of_birth,
#                         "Email": email,
#                         "Phone": phone,
#                         "Address": address,
#                         "IsTransit": is_transit,
#                         "SpecialRequirements": special_requirements
#                     })
#                     
#                     registrations.append({
#                         "PassengerID": passenger_id,
#                         "FlightNumber": flight_number
#                     })
#                 
#                 # Вставка Passengers
#                 session.run(
#                     """
#                     UNWIND $passengers AS p
#                     MERGE (passenger:Passenger {PassengerID: p.PassengerID})
#                     SET passenger.LastName = p.LastName,
#                         passenger.FirstName = p.FirstName,
#                         passenger.MiddleName = p.MiddleName,
#                         passenger.DateOfBirth = date(p.DateOfBirth),
#                         passenger.Email = p.Email,
#                         passenger.Phone = p.Phone,
#                         passenger.Address = p.Address,
#                         passenger.IsTransit = p.IsTransit,
#                         passenger.SpecialRequirements = p.SpecialRequirements
#                     """,
#                     passengers=passengers
#                 )
#                 
#                 # Вставка Relationships: REGISTERED_ON
#                 session.run(
#                     """
#                     UNWIND $registrations AS r
#                     MATCH (p:Passenger {PassengerID: r.PassengerID})
#                     MATCH (f:Flight {FlightNumber: r.FlightNumber})
#                     MERGE (p)-[:REGISTERED_ON]->(f)
#                     """,
#                     registrations=registrations
#                 )
#     
#     def main(self):
#         self.create_constraints()
#         self.populate_static_data()
#         self.populate_passengers()
#         print("Вставка данных в Neo4j завершена.")
#         self.close()
#
# if __name__ == "__main__":
#     populator = Neo4jPopulator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
#     populator.main()
