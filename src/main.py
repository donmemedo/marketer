from fastapi import FastAPI
from config import setting
from routers.plan import plan_router
from routers.fee import fee_router
from routers.volume import volume_router
from routers.user import user_router


app = FastAPI(version=setting.VERSION, title=setting.SWAGGER_TITLE)

# Add all routers
app.include_router(plan_router)
app.include_router(fee_router)
app.include_router(volume_router)
app.include_router(user_router)
