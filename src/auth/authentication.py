import aiohttp
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from jose import jwt
from src.tools.config import setting
from src.tools.logger import logger

bearer_scheme = HTTPBearer()


async def fetch_public_key() -> str:
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            async with session.get(setting.OPENID_CONFIGURATION_URL) as response:
                response.raise_for_status()
                config = await response.json()
                jwks_uri = config["jwks_uri"]
                async with session.get(jwks_uri) as jwks_response:
                    jwks_response.raise_for_status()
                    jwks = await jwks_response.json()
                    public_key = jwks["keys"][0]["x5c"][0]
                    return public_key
    except (aiohttp.ClientError, KeyError, IndexError) as err:
        logger.exception(f"Cannot connect to IDP: {err}")
        logger.error(f"Cannot connect to IDP: {err}")
        raise HTTPException(status_code=500, detail="Failed to fetch public key")


def verify_token(token: str, public_key: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_signature": False, "verify_aud": False},
        )
        return payload
    except jwt.JWTError as err:
        logger.error(f"Invalid token: {err}")
        logger.exception(f"Invalid token: {err}")
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if token.scheme != "Bearer":
        logger.exception("Invalid authentication scheme")
        logger.error("Invalid authentication scheme")
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    public_key = await fetch_public_key()
    return verify_token(token.credentials, public_key)
