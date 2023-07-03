from functools import wraps

from fastapi import HTTPException
from src.auth.permission_enum import Service
from src.tools.logger import logger


def authorize(permissions):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if kwargs.get("user").get(Service.Marketer.name):
                if not any(
                    [
                        p in kwargs.get("user").get(Service.Marketer.name)
                        for p in permissions
                    ]
                ):
                    logger.error("Unauthorized User")
                    logger.exception("Unauthorized User")
                    raise HTTPException(status_code=401, detail="Unauthorized User")
            return await func(*args, **kwargs)

        return wrapper

    return decorator
