# import pytest
# from fastapi.testclient import TestClient
# from app.models.airline import Airline
# from app.database.cassandra import cassandra_session
# from fastapi.encoders import jsonable_encoder
#
# def test_create_airline(client: TestClient, cassandra_test_session):
#     """
#     Тестирование создания авиакомпании.
#     """
#     airline_data = {
#         "AirlineID": "AL1000001",
#         "Name": "Авиакомпания Тест",
#         "Country": "Россия",
#         "ContactInfo": "contact@testairline.com"
#     }
#     
#     response = client.post("/airlines/", json=airline_data)
#     assert response.status_code == 200
#     assert response.json() == airline_data
#     
#     # Проверка в Cassandra
#     query = "SELECT * FROM airlines WHERE airlineid = %s"
#     result = cassandra_test_session.execute(query, ("AL1000001",))
#     airline = result.one()
#     assert airline is not None
#     assert airline.name == "Авиакомпания Тест"
#
# def test_get_airline(client: TestClient, cassandra_test_session):
#     """
#     Тестирование получения авиакомпании по ID.
#     """
#     airline_id = "AL1000001"
#     response = client.get(f"/airlines/{airline_id}")
#     assert response.status_code == 200
#     data = response.json()
#     assert data["AirlineID"] == airline_id
#     assert data["Name"] == "Авиакомпания Тест"
#
# def test_update_airline(client: TestClient, cassandra_test_session):
#     """
#     Тестирование обновления данных авиакомпании.
#     """
#     airline_id = "AL1000001"
#     updated_data = {
#         "AirlineID": "AL1000001",
#         "Name": "Авиакомпания Тест Обновлённая",
#         "Country": "Россия",
#         "ContactInfo": "newcontact@testairline.com"
#     }
#     
#     response = client.put(f"/airlines/{airline_id}", json=updated_data)
#     assert response.status_code == 200
#     assert response.json() == updated_data
#     
#     # Проверка в Cassandra
#     query = "SELECT * FROM airlines WHERE airlineid = %s"
#     result = cassandra_test_session.execute(query, (airline_id,))
#     airline = result.one()
#     assert airline.name == "Авиакомпания Тест Обновлённая"
#     assert airline.contactinfo == "newcontact@testairline.com"
#
# def test_delete_airline(client: TestClient, cassandra_test_session):
#     """
#     Тестирование удаления авиакомпании.
#     """
#     airline_id = "AL1000001"
#     response = client.delete(f"/airlines/{airline_id}")
#     assert response.status_code == 200
#     assert response.json() == {"detail": "Авиакомпания удалена"}
#     
#     # Проверка в Cassandra
#     query = "SELECT * FROM airlines WHERE airlineid = %s"
#     result = cassandra_test_session.execute(query, (airline_id,))
#     airline = result.one()
#     assert airline is None
#
