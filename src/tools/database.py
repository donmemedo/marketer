import os

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from tools.config import setting
from tools.logger import logger


def get_database():
    try:
        client = MongoClient(setting.MONGO_CONNECTION_STRING)
        client.server_info()
        database = client[setting.MONGO_DATABASE]
        # logger.info("Successfully connected to Mongodb")
        return database
    except ServerSelectionTimeoutError as err:
       logger.error("Cannot connect to Mongodb due to server connection timeout")
       logger.exception("Cannot connect to Mongodb due to server connection timeout")
       os.kill(os.getpid(), 9)
    except Exception as err:
       logger.error(err)
       logger.exception(err)
       os.kill(os.getpid(), 9)