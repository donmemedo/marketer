from pydantic import BaseSettings
import os

os.getenv("DOCS_URL")
class Settings(BaseSettings):
    DEFAULT_VARS = "EMTPY"
    VERSION = "0.0.1"
    MONGO_CONNECTION_STRING = "mongodb://root:1qaz1qaz@localhost:27017/"
    MONGO_DATABASE = "brokerage"
    SWAGGER_TITLE = "Marketer API"
    API_PREFIX = "/marketer"
    DOCS_URL = "/marketer/docs"


setting = Settings()
