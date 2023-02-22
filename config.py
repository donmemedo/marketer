from pydantic import BaseSettings


class Settings(BaseSettings):
    VERSION = "0.0.2"
    MONGO_CONNECTION_STRING = "mongodb://root:1qaz1qaz@192.17.240.40:27017/"
    MONGO_DATABASE = "brokerage"
    SWAGGER_TITLE = "Marketer API"
    API_PREFIX = ""
    DOCS_URL = ""
    OPENAPI_URL = ""
    ROOT_PATH = ""


setting = Settings()
