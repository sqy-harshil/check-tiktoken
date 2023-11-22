import pymongo

from config import MONGODB_URI

client = pymongo.MongoClient(MONGODB_URI)
db = client.get_default_database()

collection = db["detailed_analysis"]
