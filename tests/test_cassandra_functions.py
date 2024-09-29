# import pytest
# from fastapi.testclient import TestClient
# from app.database.cassandra import cassandra_session
# from fastapi.encoders import jsonable_encoder
#
# def test_average_tickets_per_flight(client: TestClient, cassandra_test_session):
#     """
#     Тестирование пользовательской функции Cassandra для расчёта среднего количества билетов на рейс.
#     """
#     response = client.get("/flights/average_tickets")
#     assert response.status_code == 200
#     average = response.json()
#     assert isinstance(average, float)
#     # Предположим, что в базе данных есть 2 рейса и 3 билета
#     assert average >= 1.5  # Примерная проверка
#
