import pytest
from fastapi.testclient import TestClient
from app.models.passenger import Passenger
from app.database.mongodb import passengers_collection
from fastapi.encoders import jsonable_encoder

def test_create_passenger(client: TestClient, mongodb_test_db):
    """
    Тестирование создания пассажира.
    """
    passenger_data = {
        "PassengerID": "P1000001",
        "LastName": "Иванов",
        "FirstName": "Иван",
        "MiddleName": "Иванович",
        "DateOfBirth": "1985-05-15",
        "ContactInfo": {
            "Email": "ivan.ivanov@example.com",
            "Phone": "+79991234567",
            "Address": "г. Москва, ул. Ленина, д. 1"
        },
        "IsTransit": False,
        "SpecialRequirements": ["Место у прохода"],
        "Tickets": [
            {
                "TicketNumber": "T1000001",
                "Route": {
                    "Origin": "SVO",
                    "Destination": "LED"
                },
                "DepartureTime": "2024-12-20T10:00:00Z",
                "ArrivalTime": "2024-12-20T12:00:00Z",
                "Class": "Economy",
                "Price": 800.00,
                "TicketStatus": "Confirmed",
                "Ratings": [5, 4],
                "Baggage": {
                    "BaggageNumber": "B1000001",
                    "BaggageType": "Suitcase",
                    "Weight": 20.0,
                    "BaggageStatus": "Checked",
                    "Location": "SVO"
                }
            }
        ]
    }
    
    response = client.post("/passengers/", json=passenger_data)
    assert response.status_code == 200
    assert response.json() == passenger_data
    
    # Проверка в базе данных
    passenger_in_db = passengers_collection.find_one({"PassengerID": "P1000001"})
    assert passenger_in_db is not None
    assert passenger_in_db["LastName"] == "Иванов"

def test_get_passenger(client: TestClient, mongodb_test_db):
    """
    Тестирование получения пассажира по ID.
    """
    passenger_id = "P1000001"
    response = client.get(f"/passengers/{passenger_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["PassengerID"] == passenger_id
    assert data["LastName"] == "Иванов"

def test_update_passenger(client: TestClient, mongodb_test_db):
    """
    Тестирование обновления данных пассажира.
    """
    passenger_id = "P1000001"
    updated_data = {
        "PassengerID": "P1000001",
        "LastName": "Иванов",
        "FirstName": "Иван",
        "MiddleName": "Петрович",  # Изменено
        "DateOfBirth": "1985-05-15",
        "ContactInfo": {
            "Email": "ivan.ivanov@example.com",
            "Phone": "+79991234567",
            "Address": "г. Москва, ул. Ленина, д. 1"
        },
        "IsTransit": False,
        "SpecialRequirements": ["Место у прохода", "Дополнительное место"],
        "Tickets": [
            {
                "TicketNumber": "T1000001",
                "Route": {
                    "Origin": "SVO",
                    "Destination": "LED"
                },
                "DepartureTime": "2024-12-20T10:00:00Z",
                "ArrivalTime": "2024-12-20T12:00:00Z",
                "Class": "Economy",
                "Price": 800.00,
                "TicketStatus": "Confirmed",
                "Ratings": [5, 4],
                "Baggage": {
                    "BaggageNumber": "B1000001",
                    "BaggageType": "Suitcase",
                    "Weight": 20.0,
                    "BaggageStatus": "Checked",
                    "Location": "SVO"
                }
            }
        ]
    }
    
    response = client.put(f"/passengers/{passenger_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json() == updated_data
    
    # Проверка в базе данных
    passenger_in_db = passengers_collection.find_one({"PassengerID": passenger_id})
    assert passenger_in_db["MiddleName"] == "Петрович"
    assert "Дополнительное место" in passenger_in_db["SpecialRequirements"]

def test_delete_passenger(client: TestClient, mongodb_test_db):
    """
    Тестирование удаления пассажира.
    """
    passenger_id = "P1000001"
    response = client.delete(f"/passengers/{passenger_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Пассажир удалён"}
    
    # Проверка в базе данных
    passenger_in_db = passengers_collection.find_one({"PassengerID": passenger_id})
    assert passenger_in_db is None

def test_get_passengers_with_min_tickets(client: TestClient, mongodb_test_db):
    """
    Тестирование получения пассажиров с минимальным количеством билетов.
    """
    # Создание пассажиров с разным количеством билетов
    passengers = [
        {
            "PassengerID": "P1000002",
            "LastName": "Петров",
            "FirstName": "Петр",
            "MiddleName": "Петрович",
            "DateOfBirth": "1990-03-10",
            "ContactInfo": {
                "Email": "petr.petrov@example.com",
                "Phone": "+79991234568",
                "Address": "г. Москва, ул. Пушкина, д. 2"
            },
            "IsTransit": True,
            "SpecialRequirements": [],
            "Tickets": [
                {
                    "TicketNumber": "T1000002",
                    "Route": {
                        "Origin": "SVO",
                        "Destination": "DME"
                    },
                    "DepartureTime": "2024-12-21T10:00:00Z",
                    "ArrivalTime": "2024-12-21T12:00:00Z",
                    "Class": "Business",
                    "Price": 1500.00,
                    "TicketStatus": "Confirmed",
                    "Ratings": [5],
                    "Baggage": {
                        "BaggageNumber": "B1000002",
                        "BaggageType": "Carry-on",
                        "Weight": 7.0,
                        "BaggageStatus": "Hand",
                        "Location": "SVO"
                    }
                },
                {
                    "TicketNumber": "T1000003",
                    "Route": {
                        "Origin": "DME",
                        "Destination": "LED"
                    },
                    "DepartureTime": "2024-12-22T14:00:00Z",
                    "ArrivalTime": "2024-12-22T16:00:00Z",
                    "Class": "Economy",
                    "Price": 700.00,
                    "TicketStatus": "Confirmed",
                    "Ratings": [4, 4],
                    "Baggage": {
                        "BaggageNumber": "B1000003",
                        "BaggageType": "Backpack",
                        "Weight": 12.0,
                        "BaggageStatus": "Hand",
                        "Location": "DME"
                    }
                }
            ]
        },
        {
            "PassengerID": "P1000003",
            "LastName": "Сидоров",
            "FirstName": "Сидор",
            "MiddleName": "Сидорович",
            "DateOfBirth": "1975-07-25",
            "ContactInfo": {
                "Email": "sidor.sidorov@example.com",
                "Phone": "+79991234569",
                "Address": "г. Москва, ул. Гагарина, д. 3"
            },
            "IsTransit": False,
            "SpecialRequirements": ["Питание для диабетиков"],
            "Tickets": [
                {
                    "TicketNumber": "T1000004",
                    "Route": {
                        "Origin": "LED",
                        "Destination": "SVO"
                    },
                    "DepartureTime": "2024-12-23T18:00:00Z",
                    "ArrivalTime": "2024-12-23T20:00:00Z",
                    "Class": "First",
                    "Price": 3000.00,
                    "TicketStatus": "Confirmed",
                    "Ratings": [5, 5, 4],
                    "Baggage": {
                        "BaggageNumber": "B1000004",
                        "BaggageType": "Suitcase",
                        "Weight": 25.0,
                        "BaggageStatus": "Checked",
                        "Location": "LED"
                    }
                }
            ]
        }
    ]
    
    # Вставка пассажиров
    for passenger in passengers:
        response = client.post("/passengers/", json=passenger)
        assert response.status_code == 200
    
    # Запрос пассажиров с минимум 2 билетами
    response = client.get("/passengers/tickets/count/2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["PassengerID"] == "P1000002"
    
    # Запрос пассажиров с минимум 1 билетом
    response = client.get("/passengers/tickets/count/1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

