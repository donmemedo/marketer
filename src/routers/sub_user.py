"""_summary_

Returns:
    _type_: _description_
"""
from fastapi import APIRouter, Depends, Request
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from tools import peek
from schemas import SubUserIn, SubUserOut, MarketerOut
from database import get_database
from tokens import JWTBearer, get_sub

sub_user_router = APIRouter(prefix='/subuser', tags=['Sub User'])


@sub_user_router.get("/list/", dependencies=[Depends(JWTBearer())], response_model=Page[MarketerOut])
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

    # return paginate(customer_coll, {"Referer": marketer_fullname}, sort=[("RegisterDate", -1)])
    return paginate(marketers_coll,sort=[("CreateDate", -1)])


@sub_user_router.get("/profile/", dependencies=[Depends(JWTBearer())], response_model=Page[SubUserOut])
async def get_user_profile(request: Request, args: SubUserIn = Depends(SubUserIn)):
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

@sub_user_router.get("/search/", dependencies=[Depends(JWTBearer())], response_model=Page[SubUserOut])
async def search_user_profile(request: Request, args: SubUserIn = Depends(SubUserIn)):
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

    # query = {"$and": [
    #     {"Referer": marketer_fullname},
    #     {"FirstName": {"$regex": args.first_name}},
    #     {"LastName": {"$regex": args.last_name}}
    #     ]
    # }

    filter = {
        'Referer': {
            '$regex': marketer_fullname
        },
        'FirstName': {
            '$regex': args.first_name
        },
        'LastName': {
            '$regex': args.last_name
        },
        'RegisterDate': {
            '$regex': args.register_date
        },
        'Phone': {
            '$regex': args.phone
        },
        'Mobile': {
            '$regex': args.mobile
        },
        'ID': {
            '$regex': args.user_id
        },
        'Username': {
            '$regex': args.username
        }
    }
    sort = list({
                    'BirthDate': -1
                }.items())

    # result = customer_coll.find(
    #     filter=filter,
    #     sort=sort
    # )
    # result = customer_coll.find(
    #     filter=filter
    # )
    # print(list(result))
    return paginate(customer_coll, filter, sort=[("BirthDate", -1)])



add_pagination(sub_user_router)
