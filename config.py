from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    # DEFAULT_VARS = "EMTPY"
    # VERSION = "0.0.1"
    # MONGO_CONNECTION_STRING = "mongodb://root:1qaz1qaz@localhost:27017/"
    # MONGO_DATABASE = "brokerage"
    # SWAGGER_TITLE = "Marketer API"
    # API_PREFIX = "/marketer"
    # DOCS_URL = "/marketer/docs"
    # OPENAPI_URL = "/marketer/openapi.json"
    VERSION = os.getenv("VERSION")
    MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE")
    SWAGGER_TITLE = os.getenv("SWAGGER_TITLE")
    API_PREFIX = os.getenv("API_PREFIX")
    DOCS_URL = os.getenv("DOCS_URL")
    OPENAPI_URL = os.getenv("OPENAPI_URL")

setting = Settings()
