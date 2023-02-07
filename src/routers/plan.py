from fastapi import Depends, APIRouter, Request
from serializers import marketer_entity
from database import get_database
from tokens import JWTBearer, get_sub
from schemas import CostIn, MarketerInvitationOut, MarketerInvitationIn
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate


plan_router = APIRouter(prefix='/plan', tags=['Plan and Cost'])


@plan_router.get("/marketer/", dependencies=[Depends(JWTBearer())])
async def get_marketer_profile(request: Request):
    marketer_id = get_sub(request)
    db = get_database()

    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict) 


@plan_router.get("/cost/")
async def cal_marketer_cost(args: CostIn = Depends(CostIn)):
    ...


@plan_router.put("/set-invitation-link")
async def set_marketer_invitation_link(args: MarketerInvitationIn = Depends(MarketerInvitationIn)):
    db = get_database()
    marketers_coll = db["marketers"]

    filter = {"Id": args.id}
    update = {"$set": {"InvitationLink": args.invitation_link}}

    marketers_coll.update_one(filter, update)


@plan_router.get("/list-all-marketers/", response_model=Page[MarketerInvitationOut])
async def list_all_marketers():
    db = get_database()
    marketers_coll = db["marketers"]

    return paginate(marketers_coll, {})


add_pagination(plan_router) 