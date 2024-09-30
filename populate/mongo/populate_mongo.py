import os
import random

from faker import Faker
from faker_airtravel import AirTravelProvider
from pymongo import InsertOne, MongoClient, errors
from tqdm import tqdm

fake = Faker()
fake.add_provider(AirTravelProvider)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo1:27017,mongo2:27017,mongo3:27017/?replicaSet=rs0")
NUM_RECORDS = 2000000

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

def insert_into_mongodb():
    try:
        client = MongoClient(MONGO_URI)
        db = client['AirportFlightManagement']
        passengers_collection = db['Passengers']
        
        # Настройка Bulk Write с ordered=False для повышения производительности
        batch_size = 1000
        operations = []
        
        print("Начало вставки данных в MongoDB...")
        for _ in tqdm(range(0, NUM_RECORDS, batch_size)):
            for op in generate_mongo_data(batch_size):
                operations.append(op)
            if operations:
                try:
                    passengers_collection.bulk_write(operations, ordered=False)
                except errors.BulkWriteError as bwe:
                    # Логирование ошибок вставки, но продолжение выполнения
                    print(f"Ошибка bulk_write: {bwe.details}")
                operations = []
        print("Вставка данных в MongoDB завершена.")
    except errors.ServerSelectionTimeoutError as err:
        print(f"Не удалось подключиться к MongoDB: {err}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

def main():
    insert_into_mongodb()


if __name__ == "__main__":
    main()


