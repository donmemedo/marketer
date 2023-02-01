from fastapi import FastAPI
from config import setting
from routers.plan import plan_router
from routers.fee import fee_router
from routers.volume import volume_router
from routers.user import user_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    version=setting.VERSION,
    title=setting.SWAGGER_TITLE,
    docs_url=setting.DOCS_URL
    )

origins = [
    "http://cluster.tech1a.co:9031",
    "cluster.tech1a.co:9031"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add all routers 
app.include_router(plan_router, prefix=setting.API_PREFIX)
app.include_router(fee_router, prefix=setting.API_PREFIX)
app.include_router(volume_router, prefix=setting.API_PREFIX)
app.include_router(user_router, prefix=setting.API_PREFIX)
