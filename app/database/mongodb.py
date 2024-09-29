from pymongo import MongoClient

# Настройки подключения
MONGO_URI = "mongodb://root:example@localhost:27017/"
client = MongoClient(MONGO_URI)
db = client['AirportFlightManagement']

# Коллекции
passengers_collection = db['Passengers']
tickets_collection = db['Tickets']
baggage_collection = db['Baggage']

