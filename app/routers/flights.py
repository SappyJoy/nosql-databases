from fastapi import APIRouter, HTTPException
from typing import List
from app.models.flight import Flight
from app.database.cassandra import cassandra_session
from app.database.neo4j import get_neo4j_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/flights",
    tags=["Flights"]
)

# CRUD операции

@router.post("/", response_model=Flight)
def create_flight(flight: Flight):
    logger.info(f"Создание рейса с номером: {flight.FlightNumber}")
    # Проверка уникальности FlightNumber
    query = "SELECT flightnumber FROM flights WHERE flightnumber = %s"
    result = cassandra_session.execute(query, (flight.FlightNumber,))
    if result.one():
        raise HTTPException(status_code=400, detail="FlightNumber уже существует")
    
    insert_query = """
        INSERT INTO flights (
            flightnumber,
            scheduleddeparturetime,
            scheduledarrivaltime,
            actualdeparturetime,
            actualarrivaltime,
            flightstatus,
            airlineid,
            aircraftid,
            routeid
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cassandra_session.execute(insert_query, (
        flight.FlightNumber,
        flight.ScheduledDepartureTime,
        flight.ScheduledArrivalTime,
        flight.ActualDepartureTime,
        flight.ActualArrivalTime,
        flight.FlightStatus,
        flight.AirlineID,
        flight.AircraftID,
        flight.RouteID
    ))
    
    # Дополнительно: создание связи в Neo4j (wrapper метод)
    with get_neo4j_session() as neo_session:
        cypher_query = """
            MATCH (a:Airline {AirlineID: $airline_id}),
                  (ac:Aircraft {AircraftID: $aircraft_id}),
                  (r:Route {RouteID: $route_id}),
                  (f:Flight {FlightNumber: $flight_number})
            MERGE (f)-[:OPERATED_BY]->(ac)
            MERGE (f)-[:AFFILIATED_WITH]->(a)
            MERGE (f)-[:HAS_ROUTE]->(r)
        """
        neo_session.run(cypher_query, 
                        airline_id=flight.AirlineID,
                        aircraft_id=flight.AircraftID,
                        route_id=flight.RouteID,
                        flight_number=flight.FlightNumber)
    
    return flight

@router.get("/{flight_number}", response_model=Flight)
def get_flight(flight_number: str):
    logger.info(f"Получение рейса с номером: {flight_number}")
    query = "SELECT * FROM flights WHERE flightnumber = %s"
    result = cassandra_session.execute(query, (flight_number,))
    flight = result.one()
    if not flight:
        raise HTTPException(status_code=404, detail="Рейс не найден")
    
    return Flight(
        FlightNumber=flight.flightnumber,
        ScheduledDepartureTime=flight.scheduleddeparturetime,
        ScheduledArrivalTime=flight.scheduledarrivaltime,
        ActualDepartureTime=flight.actualdeparturetime,
        ActualArrivalTime=flight.actualarrivaltime,
        FlightStatus=flight.flightstatus,
        AirlineID=flight.airlineid,
        AircraftID=flight.aircraftid,
        RouteID=flight.routeid
    )

@router.put("/{flight_number}", response_model=Flight)
def update_flight(flight_number: str, flight: Flight):
    logger.info(f"Обновление рейса с номером: {flight_number}")
    update_query = """
        UPDATE flights
        SET 
            scheduleddeparturetime = ?,
            scheduledarrivaltime = ?,
            actualdeparturetime = ?,
            actualarrivaltime = ?,
            flightstatus = ?,
            airlineid = ?,
            aircraftid = ?,
            routeid = ?
        WHERE flightnumber = ?
    """
    update_result = cassandra_session.execute(update_query, (
        flight.ScheduledDepartureTime,
        flight.ScheduledArrivalTime,
        flight.ActualDepartureTime,
        flight.ActualArrivalTime,
        flight.FlightStatus,
        flight.AirlineID,
        flight.AircraftID,
        flight.RouteID,
        flight_number
    ))
    
    if not update_result.was_applied:
        raise HTTPException(status_code=404, detail="Рейс не найден")
    
    # Обновление связей в Neo4j (wrapper метод)
    with get_neo4j_session() as neo_session:
        cypher_query = """
            MATCH (f:Flight {FlightNumber: $flight_number})
            OPTIONAL MATCH (f)-[:AFFILIATED_WITH]->(a:Airline)
            OPTIONAL MATCH (f)-[:OPERATED_BY]->(ac:Aircraft)
            OPTIONAL MATCH (f)-[:HAS_ROUTE]->(r:Route)
            SET f.FlightStatus = $flight_status
            WITH f, a, ac, r
            MERGE (a_new:Airline {AirlineID: $airline_id})
            MERGE (ac_new:Aircraft {AircraftID: $aircraft_id})
            MERGE (r_new:Route {RouteID: $route_id})
            MERGE (f)-[:AFFILIATED_WITH]->(a_new)
            MERGE (f)-[:OPERATED_BY]->(ac_new)
            MERGE (f)-[:HAS_ROUTE]->(r_new)
            DELETE f-[:AFFILIATED_WITH]->(a)
            DELETE f-[:OPERATED_BY]->(ac)
            DELETE f-[:HAS_ROUTE]->(r)
        """
        neo_session.run(cypher_query, 
                        flight_number=flight_number,
                        flight_status=flight.FlightStatus,
                        airline_id=flight.AirlineID,
                        aircraft_id=flight.AircraftID,
                        route_id=flight.RouteID)
    
    return flight

@router.delete("/{flight_number}")
def delete_flight(flight_number: str):
    logger.info(f"Удаление рейса с номером: {flight_number}")
    delete_query = "DELETE FROM flights WHERE flightnumber = ?"
    delete_result = cassandra_session.execute(delete_query, (flight_number,))
    if delete_result.was_applied:
        # Удаление связей в Neo4j (wrapper метод)
        with get_neo4j_session() as neo_session:
            cypher_query = """
                MATCH (f:Flight {FlightNumber: $flight_number})
                DETACH DELETE f
            """
            neo_session.run(cypher_query, flight_number=flight_number)
        return {"detail": "Рейс удалён"}
    else:
        raise HTTPException(status_code=404, detail="Рейс не найден")

# Дополнительные методы "обертки"

@router.get("/passenger/{passenger_id}", response_model=List[Flight])
def get_flights_by_passenger(passenger_id: str):
    logger.info(f"Получение рейсов для пассажира с ID: {passenger_id}")
    query = """
        MATCH (p:Passenger {PassengerID: $passenger_id})-[:REGISTERED_ON]->(f:Flight)
        RETURN f
    """
    with get_neo4j_session() as neo_session:
        result = neo_session.run(query, passenger_id=passenger_id)
        flights = []
        for record in result:
            f = record["f"]
            flights.append(Flight(
                FlightNumber=f["FlightNumber"],
                ScheduledDepartureTime=f["ScheduledDepartureTime"],
                ScheduledArrivalTime=f["ScheduledArrivalTime"],
                ActualDepartureTime=f.get("ActualDepartureTime"),
                ActualArrivalTime=f.get("ActualArrivalTime"),
                FlightStatus=f["FlightStatus"],
                AirlineID=f["AirlineID"],
                AircraftID=f["AircraftID"],
                RouteID=f["RouteID"]
            ))
    return flights

@router.get("/average_tickets", response_model=float)
def get_average_tickets_per_flight():
    logger.info(f"Получение среднего количества билетов на рейс")
    # Пример использования функции (если была создана пользовательская функция в Cassandra)
    query = "SELECT airportflightmanagement.avg_tickets_per_flight() AS average"
    result = cassandra_session.execute(query)
    row = result.one()
    if row and row.average is not None:
        return row.average
    else:
        raise HTTPException(status_code=500, detail="Не удалось вычислить среднее количество билетов")
