# app/models/passenger.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime

class Baggage(BaseModel):
    BaggageNumber: str
    BaggageType: str
    Weight: float
    BaggageStatus: str
    Location: str

class Ticket(BaseModel):
    TicketNumber: str
    Route: dict  # Можно создать отдельную модель для маршрута
    DepartureTime: datetime
    ArrivalTime: datetime
    Class: str
    Price: float
    TicketStatus: str
    Ratings: List[int]
    Baggage: Baggage

class ContactInfo(BaseModel):
    Email: EmailStr
    Phone: str
    Address: str

class Passenger(BaseModel):
    PassengerID: str
    LastName: str
    FirstName: str
    MiddleName: Optional[str]
    DateOfBirth: date
    ContactInfo: ContactInfo
    IsTransit: bool
    SpecialRequirements: Optional[List[str]]
    Tickets: List[Ticket]

