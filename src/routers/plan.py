from fastapi import Depends, APIRouter, Request
from serializers import marketer_entity
from database import get_database
from tokens import JWTBearer, get_sub


plan_router = APIRouter(prefix='/plan', tags=['plan'])


@plan_router.get("/marketer/", dependencies=[Depends(JWTBearer())])
async def get_marketer_profile(request: Request):
    marketer_id = get_sub(request)
    db = get_database()

    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict) 


# TODO: implement marketers' costs
@plan_router.get("/marketer_costs/")
async def cal_marketer_costs():
    pass
