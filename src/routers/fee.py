from fastapi import Depends, HTTPException, APIRouter, Request
from database import get_database
from tools import remove_id, to_gregorian, peek
from schemas import UserFee, UserTotalFee
from tokens import JWTBearer, get_sub
from serializers import fee_entity


fee_router = APIRouter(prefix='/fee', tags=['fee'])


@fee_router.get("/user", dependencies=[Depends(JWTBearer())])
async def get_user_fee(request: Request, args: UserFee = Depends(UserFee)):
    # get user id
    marketer_id = get_sub(request)    
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]
    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": marketer_dict.get("FirstName")}},
        {"PAMCode": args.trade_code}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c for c in customers_records]

    if not trade_codes:
        return {"TotalVolume": 0}
    else:
        pipeline = [
            {"$match": {"TradeCode": args.trade_code}},
            {
                "$group": {
                    "_id": "$id", 
                    "TotalFee": {
                        "$sum": "$TradeItemBroker"
                        }
                    }
                },
            ]
         
        agg_result = trades_coll.aggregate(pipeline=pipeline)

        fee_dict = next(agg_result, {"TotalFee": 0})
        
        return fee_entity(fee_dict)


@fee_router.get("/users/", dependencies=[Depends(JWTBearer())])
async def get_users_total_fee(request: Request, args: UserTotalFee = Depends(UserTotalFee)):
    # get user id
    marketer_id = get_sub(request)    

    db = get_database()

    marketer_coll = db["marketers"]
    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # check if marketer exists and return his name
    query_result = marketer_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    # Check if customer exists
    query = {"$and": [
        {"Referer": {"$regex": marketer_dict.get('FirstName')}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    gregorian_date = to_gregorian(args.from_date)
    print(gregorian_date) 
    pipeline = [
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gte": gregorian_date}}
                    ]
                }
            },
        {
            "$group": {
                "_id": "$id", 
                "TotalFee": {
                    "$sum": "$TradeItemBroker"
                    }
                }
        },
        {
            "$project": {
                "_id": 0
            }
        }
    ]

    agg_result = peek(trades_coll.aggregate(pipeline=pipeline))

    if agg_result is not None:
        return agg_result
    else:
        return {"TotalFee": 0 }
