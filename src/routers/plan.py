from fastapi import Depends, APIRouter
import uvicorn
from schemas import *
from tools import remove_id
from database import get_database


plan_router = APIRouter(prefix='/plan', tags=['plan'])


@plan_router.get("/marketer/")
async def get_marketer_profile(args: MarketerIn = Depends(MarketerIn)):
    db = get_database()

    marketers_coll = db["marketers"]
    query = {"FirstName": {"$regex": args.name}}

    query_result = marketers_coll.find(query)
    return remove_id([r for r in query_result])


# TODO: implement marketers' costs
@plan_router.get("/marketer_costs/")
async def cal_marketer_costs():
    pass
