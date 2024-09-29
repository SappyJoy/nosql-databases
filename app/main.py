from fastapi import FastAPI
from app.routers import passengers, flights
from fastapi.middleware.cors import CORSMiddleware

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

# Включение роутеров
app.include_router(passengers.router)
app.include_router(flights.router)

@app.get("/")
def read_root():
    return {"message": "Добро пожаловать в API системы управления полетами аэропорта"}

