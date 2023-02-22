"""_summary_

Returns:
    _type_: _description_
"""
from fastapi import Depends, APIRouter, Request
from database import get_database
from tools import to_gregorian, peek
from schemas import UserFee
from tokens import JWTBearer, get_sub
from serializers import fee_entity


fee_router = APIRouter(prefix='/fee', tags=['fee'])


@fee_router.get("/user", dependencies=[Depends(JWTBearer())])
async def get_user_fee(request: Request, args: UserFee = Depends(UserFee)):
    """_summary_

    Args:
        request (Request): _description_
        args (UserFee, optional): _description_. Defaults to Depends(UserFee).

    Returns:
        _type_: _description_
    """
    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()

    customers_coll = brokerage["customers"]
    trades_coll = brokerage["trades"]
    marketers_coll = brokerage["marketers"]

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
    # trade_codes = [c for c in customers_records]
    trade_codes = []
    for customer in customers_records:
        trade_codes.append(customer)

    from_gregorian_date = to_gregorian(args.from_date)
    to_gregorian_date = to_gregorian(args.to_date)

    if not trade_codes:
        return {"TotalVolume": 0}
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
