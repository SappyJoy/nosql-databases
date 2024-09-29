from pydantic import BaseModel

class Route(BaseModel):
    RouteID: str
    Origin: str
    Destination: str
    Distance: float
    TravelTime: int

