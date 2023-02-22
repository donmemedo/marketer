"""_summary_

Returns:
    _type_: _description_
"""
from fastapi import APIRouter, Depends, Request
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from tools import peek
from schemas import UserIn, UserOut
from database import get_database
from tokens import JWTBearer, get_sub

user_router = APIRouter(prefix='/user', tags=['User'])


@user_router.get("/list/", dependencies=[Depends(JWTBearer())], response_model=Page[UserOut])
async def search_marketer_user(request: Request):
    """_summary_

    Args:
        request (Request): _description_

    Returns:
        _type_: _description_
    """
    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()
    customer_coll = brokerage["customers"]
    marketers_coll = brokerage["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})
    marketer_dict = peek(query_result)
    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")

    return paginate(customer_coll, {"Referer": marketer_fullname}, sort=[("RegisterDate", -1)])


@user_router.get("/profile/", dependencies=[Depends(JWTBearer())], response_model=Page[UserOut])
async def get_user_profile(request: Request, args: UserIn = Depends(UserIn)):
    """_summary_

    Args:
        request (Request): _description_
        args (UserIn, optional): _description_. Defaults to Depends(UserIn).

    Returns:
        _type_: _description_
    """
    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()

    customer_coll = brokerage["customers"]
    marketers_coll = brokerage["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")

    query = {"$and": [
        {"Referer": marketer_fullname},
        {"FirstName": {"$regex": args.first_name}},
        {"LastName": {"$regex": args.last_name}}
        ]
    }

    return paginate(customer_coll, query, sort=[("RegisterDate", -1)])


add_pagination(user_router)
