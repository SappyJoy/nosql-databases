from fastapi import FastAPI
from routers import passengers, flights
from fastapi.middleware.cors import CORSMiddleware
from database.mongodb import client as mongodb_client
from database.cassandra import cassandra_session
from database.neo4j import driver as neo4j_driver, close_driver


app = FastAPI(
    title="Airport Flight Management API",
    description="API для управления данными аэропорта с использованием MongoDB, Cassandra и Neo4j",
    version="1.0.0"
)

# Разрешение CORS (при необходимости)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Настройте по необходимости
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Включение маршрутов
app.include_router(flights.router)
app.include_router(passengers.router)

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в API системы управления полетами аэропорта"}

@app.on_event("startup")
async def startup_event():
    print("Приложение запускается и подключается к базам данных.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Приложение завершается и закрывает подключения к базам данных.")
    mongodb_client.close()
    cassandra_session.shutdown()
    close_driver()
