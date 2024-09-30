from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError
from typing import List
import logging
from models.passenger import Passenger
from database.mongodb import passengers_collection
from fastapi.encoders import jsonable_encoder  # Добавлен импорт

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/passengers",
    tags=["Passengers"]
)

# Преобразование MongoDB документа в Pydantic модель
def passenger_helper(passenger) -> Passenger:
    return Passenger(
        PassengerID=passenger["PassengerID"],
        LastName=passenger["LastName"],
        FirstName=passenger["FirstName"],
        MiddleName=passenger.get("MiddleName"),
        DateOfBirth=passenger["DateOfBirth"],
        ContactInfo=passenger["ContactInfo"],
        IsTransit=passenger["IsTransit"],
        SpecialRequirements=passenger.get("SpecialRequirements"),
        Tickets=passenger["Tickets"]
    )

# CRUD операции
@router.post("/", response_model=Passenger)
def create_passenger(passenger: Passenger):
    logger.info(f"Создание пассажира с ID: {passenger.PassengerID}")
    # Проверка уникальности PassengerID
    if passengers_collection.find_one({"PassengerID": passenger.PassengerID}):
        raise HTTPException(status_code=400, detail="PassengerID уже существует")
    
    try:
        # Использование jsonable_encoder для преобразования данных
        passenger_dict = jsonable_encoder(passenger.dict())
        passengers_collection.insert_one(passenger_dict)
        return passenger
    except PyMongoError as e:
        logger.error(f"Ошибка при вставке пассажира: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при вставке пассажира в базу данных")

@router.get("/{passenger_id}", response_model=Passenger)
def get_passenger(passenger_id: str):
    logger.info(f"Получение пассажира с ID: {passenger_id}")
    passenger = passengers_collection.find_one({"PassengerID": passenger_id})
    if not passenger:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    return passenger_helper(passenger)

@router.put("/{passenger_id}", response_model=Passenger)
def update_passenger(passenger_id: str, passenger: Passenger):
    logger.info(f"Обновление пассажира с ID: {passenger_id}")
    update_result = passengers_collection.update_one(
        {"PassengerID": passenger_id},
        {"$set": passenger.dict(exclude_unset=True)}
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    
    updated_passenger = passengers_collection.find_one({"PassengerID": passenger_id})
    return passenger_helper(updated_passenger)

@router.delete("/{passenger_id}")
def delete_passenger(passenger_id: str):
    logger.info(f"Удаление пассажира с ID: {passenger_id}")
    delete_result = passengers_collection.delete_one({"PassengerID": passenger_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Пассажир не найден")
    return {"detail": "Пассажир удалён"}

# Дополнительные методы "обертки"

@router.get("/tickets/count/{min_tickets}", response_model=List[Passenger])
def get_passengers_with_min_tickets(min_tickets: int):
    logger.info(f"Получение пассажиров с количеством билетов не менее {min_tickets}")
    pipeline = [
        {"$match": {"Tickets": {"$exists": True}}},
        {"$project": {
            "PassengerID": 1,
            "LastName": 1,
            "FirstName": 1,
            "MiddleName": 1,
            "DateOfBirth": 1,
            "ContactInfo": 1,
            "IsTransit": 1,
            "SpecialRequirements": 1,
            "Tickets": 1,
            "tickets_count": {"$size": "$Tickets"}
        }},
        {"$match": {"tickets_count": {"$gte": min_tickets}}}
    ]
    
    passengers = passengers_collection.aggregate(pipeline)
    logger.info(f"Найдено пассажиров: {passengers.count()}")
    return [passenger_helper(p) for p in passengers]
