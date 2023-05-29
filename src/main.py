from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tools.config import setting
from routers.plan import plan_router
from routers.volume_and_fee import volume_and_fee_router
from routers.user import user_router


app = FastAPI(
    version=setting.VERSION,
    title=setting.SWAGGER_TITLE,
)

origins = ["*"]

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
