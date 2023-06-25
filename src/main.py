from logging.config import dictConfig

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth.permissions import permissions
from auth.registration import get_token, set_permissions
from routers.plan import plan_router
from routers.user import user_router
from routers.volume_and_fee import volume_and_fee_router
from tools.config import setting
from tools.logger import log_config

app = FastAPI(
    version=setting.VERSION,
    title=setting.SWAGGER_TITLE,
    docs_url=setting.FASTAPI_DOCS,
    redoc_url=setting.FASTAPI_REDOC,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=setting.ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    token = await get_token()
    await set_permissions(permissions, token)


@app.get("/health-check", tags=["Default"])
def health_check():
    return {"status": "OK"}


# Add all routers
app.include_router(plan_router, prefix="")
app.include_router(volume_and_fee_router, prefix="")
app.include_router(user_router, prefix="")


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000, log_config=dictConfig(log_config))
