from pydantic import BaseModel

class Airline(BaseModel):
    AirlineID: str
    Name: str
    Country: str
    ContactInfo: str

