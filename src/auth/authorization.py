from datetime import datetime
from functools import wraps

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from src.schemas.schemas import ErrorOut
from src.tools.logger import logger
from src.tools.messages import errors


def authorize(permissions):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not isinstance(kwargs.get("user"), dict) or not any(
                    [
                        p in kwargs.get("user").get("permission", [])
                        for p in permissions
                    ]
            ):
                logger.error("Unauthorized User")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=jsonable_encoder(
                        ErrorOut(
                            error=errors.get("MARKETER_NOT_DEFINED2"),
                            timeGenerated=datetime.now(),
                            result={}
                        )
                    )
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
