from pydantic import BaseSettings


class Settings(BaseSettings):
    VERSION = "0.0.1"
    MONGO_CONNECTION_STRING = "mongodb://root:1qaz1qaz@localhost:27017/"
    MONGO_DATABASE = "brokerage"
    SWAGGER_TITLE = "Marketer API"
    SPLUNK_HOST = "172.24.65.206"
    SPLUNK_PORT = 5141
    FASTAPI_DOCS = "/docs"
    FASTAPI_REDOC = "/redoc"
    FACTORS_COLLECTION = "napfactorsss"
    ORIGINS = "*"
    TOKEN_URL = "https://cluster.tech1a.co/connect/token"
    CLIENT_ID = "M2M.RegisterServicePermission"
    CLIENT_SECRET = "IDPRegisterServicePermission"
    GRANT_TYPE = "client_credentials"
    OPENID_CONFIGURATION_URL = (
        "https://cluster.tech1a.co/.well-known/openid-configuration"
    )
    REGISTRATION_URL = (
        "https://cluster.tech1a.co/api/service-permossion/register-service-permission"
    )


setting = Settings()
