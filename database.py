from pymongo import MongoClient
from config import setting


def get_database():
    client = MongoClient(setting.MONGO_CONNECTION_STRING)

    db = client[setting.MONGO_DATABASE]

    return db
