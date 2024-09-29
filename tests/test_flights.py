import pytest
from fastapi.testclient import TestClient
from app.models.flight import Flight
from app.database.cassandra import cassandra_session
from app.database.neo4j import neo4j_driver
from fastapi.encoders import jsonable_encoder

def test_create_flight(client: TestClient, cassandra_test_session, neo4j_test_driver):
    """
    Тестирование создания рейса.
    """
    flight_data = {
        "FlightNumber": "FL2000001",
        "ScheduledDepartureTime": "2024-12-25T08:00:00",
        "ScheduledArrivalTime": "2024-12-25T12:00:00",
        "ActualDepartureTime": "2024-12-25T08:05:00",
        "ActualArrivalTime": "2024-12-25T12:10:00",
        "FlightStatus": "Confirmed",
        "AirlineID": "AL0001",
        "AircraftID": "AC00001",
        "RouteID": "R00001"
    }
    
    response = client.post("/flights/", json=flight_data)
    assert response.status_code == 200
    assert response.json() == flight_data
    
    # Проверка в Cassandra
    query = "SELECT * FROM flights WHERE flightnumber = %s"
    result = cassandra_test_session.execute(query, ("FL2000001",))
    flight = result.one()
    assert flight is not None
    assert flight.flightstatus == "Confirmed"
    
    # Проверка связей в Neo4j
    with neo4j_test_driver.session() as session:
        cypher_query = """
            MATCH (f:Flight {FlightNumber: $flight_number})-[:AFFILIATED_WITH]->(a:Airline),
                  (f)-[:OPERATED_BY]->(ac:Aircraft),
                  (f)-[:HAS_ROUTE]->(r:Route)
            RETURN a, ac, r
        """
        result = session.run(cypher_query, flight_number="FL2000001")
        record = result.single()
        assert record is not None
        assert record["a"]["AirlineID"] == "AL0001"
        assert record["ac"]["AircraftID"] == "AC00001"
        assert record["r"]["RouteID"] == "R00001"

def test_get_flight(client: TestClient, cassandra_test_session):
    """
    Тестирование получения рейса по номеру.
    """
    flight_number = "FL2000001"
    response = client.get(f"/flights/{flight_number}")
    assert response.status_code == 200
    data = response.json()
    assert data["FlightNumber"] == flight_number
    assert data["FlightStatus"] == "Confirmed"

def test_update_flight(client: TestClient, cassandra_test_session, neo4j_test_driver):
    """
    Тестирование обновления рейса.
    """
    flight_number = "FL2000001"
    updated_data = {
        "FlightNumber": "FL2000001",
        "ScheduledDepartureTime": "2024-12-25T08:00:00",
        "ScheduledArrivalTime": "2024-12-25T12:00:00",
        "ActualDepartureTime": "2024-12-25T08:10:00",  # Изменено
        "ActualArrivalTime": "2024-12-25T12:15:00",    # Изменено
        "FlightStatus": "Delayed",                     # Изменено
        "AirlineID": "AL0002",                         # Изменено
        "AircraftID": "AC00002",                       # Изменено
        "RouteID": "R00002"                             # Изменено
    }
    
    response = client.put(f"/flights/{flight_number}", json=updated_data)
    assert response.status_code == 200
    assert response.json() == updated_data
    
    # Проверка в Cassandra
    query = "SELECT * FROM flights WHERE flightnumber = %s"
    result = cassandra_test_session.execute(query, (flight_number,))
    flight = result.one()
    assert flight is not None
    assert flight.flightstatus == "Delayed"
    
    # Проверка обновленных связей в Neo4j
    with neo4j_test_driver.session() as session:
        cypher_query = """
            MATCH (f:Flight {FlightNumber: $flight_number})-[:AFFILIATED_WITH]->(a:Airline),
                  (f)-[:OPERATED_BY]->(ac:Aircraft),
                  (f)-[:HAS_ROUTE]->(r:Route)
            RETURN a, ac, r
        """
        result = session.run(cypher_query, flight_number=flight_number)
        record = result.single()
        assert record is not None
        assert record["a"]["AirlineID"] == "AL0002"
        assert record["ac"]["AircraftID"] == "AC00002"
        assert record["r"]["RouteID"] == "R00002"

def test_delete_flight(client: TestClient, cassandra_test_session, neo4j_test_driver):
    """
    Тестирование удаления рейса.
    """
    flight_number = "FL2000001"
    response = client.delete(f"/flights/{flight_number}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Рейс удалён"}
    
    # Проверка в Cassandra
    query = "SELECT * FROM flights WHERE flightnumber = %s"
    result = cassandra_test_session.execute(query, (flight_number,))
    flight = result.one()
    assert flight is None
    
    # Проверка удаления узлов и связей в Neo4j
    with neo4j_test_driver.session() as session:
        cypher_query = """
            MATCH (f:Flight {FlightNumber: $flight_number})
            RETURN f
        """
        result = session.run(cypher_query, flight_number=flight_number)
        record = result.single()
        assert record is None

def test_get_flights_by_passenger(client: TestClient, cassandra_test_session, neo4j_test_driver, mongodb_test_db):
    """
    Тестирование получения рейсов, связанных с пассажиром.
    """
    # Создание пассажира и связанного рейса
    passenger_data = {
        "PassengerID": "P1000004",
        "LastName": "Кузнецов",
        "FirstName": "Павел",
        "MiddleName": "Сергеевич",
        "DateOfBirth": "1992-11-30",
        "ContactInfo": {
            "Email": "pavel.kuznetsov@example.com",
            "Phone": "+79991234570",
            "Address": "г. Москва, ул. Толстого, д. 4"
        },
        "IsTransit": False,
        "SpecialRequirements": [],
        "Tickets": [
            {
                "TicketNumber": "T1000005",
                "Route": {
                    "Origin": "SVO",
                    "Destination": "LED"
                },
                "DepartureTime": "2024-12-26T09:00:00Z",
                "ArrivalTime": "2024-12-26T11:00:00Z",
                "Class": "Economy",
                "Price": 750.00,
                "TicketStatus": "Confirmed",
                "Ratings": [4, 5],
                "Baggage": {
                    "BaggageNumber": "B1000005",
                    "BaggageType": "Backpack",
                    "Weight": 15.0,
                    "BaggageStatus": "Hand",
                    "Location": "SVO"
                }
            }
        ]
    }
    
    # Создание пассажира
    response = client.post("/passengers/", json=passenger_data)
    assert response.status_code == 200
    
    # Создание рейса
    flight_data = {
        "FlightNumber": "FL2000002",
        "ScheduledDepartureTime": "2024-12-26T09:00:00",
        "ScheduledArrivalTime": "2024-12-26T11:00:00",
        "ActualDepartureTime": "2024-12-26T09:05:00",
        "ActualArrivalTime": "2024-12-26T11:10:00",
        "FlightStatus": "Confirmed",
        "AirlineID": "AL0001",
        "AircraftID": "AC00001",
        "RouteID": "R00001"
    }
    
    response = client.post("/flights/", json=flight_data)
    assert response.status_code == 200
    
    # Регистрация пассажира на рейс в MongoDB (эмулируем связь)
    passengers_collection.update_one(
        {"PassengerID": "P1000004"},
        {"$push": {"Tickets": {
            "TicketNumber": "T1000005",
            "Route": {
                "Origin": "SVO",
                "Destination": "LED"
            },
            "DepartureTime": "2024-12-26T09:00:00Z",
            "ArrivalTime": "2024-12-26T11:00:00Z",
            "Class": "Economy",
            "Price": 750.00,
            "TicketStatus": "Confirmed",
            "Ratings": [4, 5],
            "Baggage": {
                "BaggageNumber": "B1000005",
                "BaggageType": "Backpack",
                "Weight": 15.0,
                "BaggageStatus": "Hand",
                "Location": "SVO"
            }
        }}}
    )
    
    # Вызов метода "обертки" для получения рейсов пассажира
    response = client.get("/flights/passenger/P1000004")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["FlightNumber"] == "FL2000002"

