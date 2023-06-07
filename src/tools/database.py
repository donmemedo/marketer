from pymongo import MongoClient
from tools.config import setting


def get_database():
    client = MongoClient(setting.MONGO_CONNECTION_STRING)

    database = client[setting.MONGO_DATABASE]

    return database
