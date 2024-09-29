from pydantic import BaseModel

class Airport(BaseModel):
    AirportCode: str
    Name: str
    City: str
    Country: str
    ContactInfo: str

