import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.plan import plan_router
from routers.user import user_router
from routers.volume_and_fee import volume_and_fee_router
from tools.config import setting
from tools.logger import logger

app = FastAPI(
    version=setting.VERSION,
    title=setting.SWAGGER_TITLE,
    docs_url=setting.FASTAPI_DOCS,
    redoc_url=setting.FASTAPI_REDOC
)

origins = [setting.ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health-check", tags=["Deafult"])
def health_check():
    return {"status": "OK"}


# Add all routers
app.include_router(plan_router, prefix="")
app.include_router(volume_and_fee_router, prefix="")
app.include_router(user_router, prefix="")


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)