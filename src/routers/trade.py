from fastapi import Depends, APIRouter
import uvicorn
from schemas import *
from tools import remove_id
from database import get_database


trade_router = APIRouter(prefix='/plan', tags=['plan'])


@trade_router.get("/marketer/")
async def get_marketer_profile(args: MarketerIn = Depends(MarketerIn)):
    db = get_database()

    marketers_coll = db["marketers"]
    query = {"FirstName": {"$regex": args.name}}

    query_result = marketers_coll.find(query)
    return remove_id([r for r in query_result])


# TODO: implement marketers' costs
@trade_router.get("/marketer_costs/")
async def cal_marketer_costs():
    pass


if __name__ == "__main__":
    uvicorn.run(app=trade_router, host="0.0.0.0", port=8000)

    # TODO: use motor to async all database connections
    # TODO: add response model to all APIs
