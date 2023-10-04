from datetime import datetime

import aiohttp
from fastapi import Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from jose import jwt

from src.schemas.schemas import ErrorOut
from src.tools.config import setting
from src.tools.logger import logger
from src.tools.messages import errors

bearer_scheme = HTTPBearer()


async def fetch_public_key() -> str | JSONResponse:
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

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("CANNOT_FETCH_PUBLIC_KEY"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )


def verify_token(token: str, public_key: str) -> dict | JSONResponse:
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_signature": False, "verify_aud": False},
        )
        return payload

    except jwt.ExpiredSignatureError as err:
        logger.error(f"Expired token: {err}")

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("TOKEN_EXPIRED"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )

    except jwt.JWTError as err:
        logger.error(f"Invalid token: {err}")

        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("MARKETER_NOT_DEFINED"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )


async def get_current_user(
        token: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict | JSONResponse:
    if token.scheme != "Bearer":
        logger.error("Invalid authentication scheme")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("INVALID_AUTHENTICATION_SCHEME"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )
    public_key = await fetch_public_key()
    return verify_token(token.credentials, public_key)
