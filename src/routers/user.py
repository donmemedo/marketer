from fastapi import APIRouter, Depends, Request
from tools import remove_id, peek
from schemas import UserIn, UserOut
from database import get_database
from tokens import JWTBearer, get_sub
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate


user_router = APIRouter(prefix='/user', tags=['User'])


@user_router.get("/list/", dependencies=[Depends(JWTBearer())], response_model=Page[UserOut])
async def search_marketer_user(request: Request):
    marketer_id = get_sub(request)  
    db = get_database()

    customer_coll = db["customers"]
    marketers_coll = db["marketers"]


    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    query = {
        "Referer": {
            "$regex": marketer_dict.get("FirstName")
            }
        }

    return paginate(customer_coll, {})


add_pagination(user_router)

@user_router.get("/profile/", dependencies=[Depends(JWTBearer())])
async def get_user_profile(request: Request, args: UserIn = Depends(UserIn)):
    # get user id
    marketer_id = get_sub(request)
    db = get_database()

    customer_coll = db["customers"]
    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    query = {"$and": [
        {"Referer": {"$regex": marketer_dict.get("FistName")}},
        {"FirstName": {"$regex": args.first_name}},
        {"LastName": {"$regex": args.last_name }}
        ]
    }

    fields = {
        "Username": 1,
        "PAMCode": 1
    }

    total_records = customer_coll.count_documents(query)

    docs = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)
    response = [d for d in docs]

    remove_id(response)
    return { "TotalRecords": total_records, "Response": response}
