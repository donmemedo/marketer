from fastapi import APIRouter, Depends, Request
from tools import to_gregorian, remove_id, peek
from schemas import SearchUserIn, UserIn
from database import get_database
from datetime import date, timedelta
from tokens import JWTBearer, get_sub
from serializers import marketer_entity
from collections import defaultdict


user_router = APIRouter(prefix='/user', tags=['user'])


@user_router.get("/list/", dependencies=[Depends(JWTBearer())])
async def search_marketer_user(request: Request, args: SearchUserIn = Depends(SearchUserIn)):
    marketer_id = get_sub(request)  
    db = get_database()

    customer_coll = db["customers"]
    marketers_coll = db["marketers"]
    trades_coll = db["trades"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    query = {"Referer": {"$regex": marketer_dict.get("FirstName")}}

    fields = {
        "Username": 1,
        "FirstName": 1,
        "LastName": 1,
        "PAMCode": 1,
        "BankAccountNumber": 1,
    }

    docs = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)
    total_records = customer_coll.count_documents(query)
    users = [doc for doc in docs]

    remove_id(users)

    # TODO: currently we consider all users as customer, in future this must change
    for item in users:
        item.update({"UserType": "مشتری"})


    # get last month starting date
    today = date.today()
    last_month = today - timedelta(days=30)
    temporary = last_month.strftime("%Y-%m-%d")

    trade_codes = [user.get('PAMCode') for user in users]

    # Calculate users volumes

    pipeline = [
        {
            "$match": {"$and": [
                {"TradeCode": {"$in": trade_codes}}
            ]}
        },
        {
            "$group": {
                "_id": "$TradeCode",
                "TotalVolume": {"$sum": {"$multiply": ["$Price", "$Volume"]}}
            }
        },
        {
            "$project": {
                "_id": 0,
                "PAMCode": "$_id",
                "TotalVolume": 1
            }
        }
    ]

    aggr_result = trades_coll.aggregate(pipeline=pipeline)

    volume_list = list(aggr_result)

    
    users_dict = {u["PAMCode"]: u for u in users}

    for v in volume_list:
        users_dict.get(v["PAMCode"]).update(v)

    return {
        "Results": list(users_dict.values()),
        "TotalRecords": total_records
    }


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
