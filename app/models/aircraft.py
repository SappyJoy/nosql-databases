from pydantic import BaseModel

class Aircraft(BaseModel):
    AircraftID: str
    Model: str
    Manufacturer: str
    YearOfManufacture: int
    Capacity: int
    Specifications: str

