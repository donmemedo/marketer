from pydantic import BaseSettings


class Settings(BaseSettings):
    VERSION = "0.0.1"
    MONGO_CONNECTION_STRING = "mongodb://root:1qaz1qaz@localhost:27017/"
    MONGO_DATABASE = "brokerage"
    SWAGGER_TITLE = "Marketer API"
    API_PREFIX = ""
    DOCS_URL = ""
    OPENAPI_URL = ""
    ROOT_PATH = ""
    JWKS = ""
    ISSUER = "https://cluster.tech1a.co"


setting = Settings()
