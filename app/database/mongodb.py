import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Настройки подключения
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Попытка подключиться к серверу
    client.admin.command('ping')
    print("Подключение к MongoDB успешно.")
    db = client['AirportFlightManagement']

# Коллекции
    passengers_collection = db['Passengers']
    tickets_collection = db['Tickets']
    baggage_collection = db['Baggage']
except ServerSelectionTimeoutError as err:
    print(f"Не удалось подключиться к MongoDB: {err}")
    # Здесь можно добавить логику для повторной попытки подключения
