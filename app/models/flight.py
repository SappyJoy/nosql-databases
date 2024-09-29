from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Flight(BaseModel):
    FlightNumber: str
    ScheduledDepartureTime: datetime
    ScheduledArrivalTime: datetime
    ActualDepartureTime: Optional[datetime]
    ActualArrivalTime: Optional[datetime]
    FlightStatus: str
    AirlineID: str
    AircraftID: str
    RouteID: str

