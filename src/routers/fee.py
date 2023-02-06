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

    from_gregorian_date = to_gregorian(args.from_date)
    to_gregorian_date = to_gregorian(args.to_date)

    if not trade_codes:
        return {"TotalVolume": 0}
    else:
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"TradeCode": args.trade_code}, 
                        {"TradeDate": {"$gte": from_gregorian_date}},
                        {"TradeDate": {"$lte": to_gregorian_date}}
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
            ]
         
        agg_result = trades_coll.aggregate(pipeline=pipeline)

        fee_dict = next(agg_result, {"TotalFee": 0})
        
        return fee_entity(fee_dict)
