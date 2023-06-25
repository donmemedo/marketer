from pydantic import BaseSettings


class Settings(BaseSettings):
    VERSION = "0.0.1"
    MONGO_CONNECTION_STRING = "mongodb://root:root@172.24.65.106:30001/"
    MONGO_DATABASE = "brokerage"
    SWAGGER_TITLE = "Marketer API"
    API_PREFIX = ""
    DOCS_URL = ""
    OPENAPI_URL = ""
    ROOT_PATH = ""
    JWKS = ""
    ISSUER = "https://cluster.tech1a.co"


setting = Settings()
