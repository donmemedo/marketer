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
    JWKS_CONFIGURATION_URL = "https://cluster.tech1a.co/.well-known/openid-configuration/jwks"
    ISSUER = "https://cluster.tech1a.co"
    APPLICATION_ID = "d7f48c21-2a19-4bdb-ace8-48928bff0eb5"
    SPLUNK_HOST = "172.24.65.206"
    SPLUNK_PORT = 5141
    SPLUNK_INDEX = "dev"

setting = Settings()
