from fastapi import APIRouter, Depends, Request
from tools import remove_id, peek
from schemas import UserIn, UserOut
from database import get_database
from tokens import JWTBearer, get_sub
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate


user_router = APIRouter(prefix='/user', tags=['User'])


@user_router.get("/list/", dependencies=[Depends(JWTBearer())], response_model=Page[UserOut])
async def search_marketer_user():
    db = get_database()

    customer_coll = db["customers"]

    return paginate(customer_coll, {})


@user_router.get("/profile/", dependencies=[Depends(JWTBearer())], response_model=Page[UserOut])
async def get_user_profile(request: Request, args: UserIn = Depends(UserIn)):
    # get user id
    marketer_id = get_sub(request)
    db = get_database()

    customer_coll = db["customers"]
    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = marketer_dict.get("FirstName") + ' ' + marketer_dict.get("LastName")

    query = {"$and": [
        {"Referer": marketer_fullname}, 
        {"FirstName": {"$regex": args.first_name}}, 
        {"LastName": {"$regex": args.last_name}} 
        ]
    }
    return paginate(customer_coll, query)

add_pagination(user_router)
