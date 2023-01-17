from fastapi import Depends, HTTPException, APIRouter
from database import get_database
from tools import remove_id, to_gregorian, peek
from schemas import UserFee, UserTotalFee


fee_router = APIRouter(prefix='/fee', tags=['fee'])


@fee_router.get("/user")
async def get_user_fee(args: UserFee = Depends(UserFee)):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}},
        {"PAMCode": args.trade_code}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c for c in customers_records]

    if not trade_codes:
        raise HTTPException(status_code=404, detail="Customer Not Found")
    else:
        pipeline = [
            {"$match": {"TradeCode": args.trade_code}},
            {
                "$group": {
                    "_id": "$id", 
                    "TotalVolume": {
                        "$sum": "$TradeItemBroker"
                        }
                    }
                },
            ]
         
        agg_result = trades_coll.aggregate(pipeline=pipeline)

        return (remove_id([a for a in agg_result]))


@fee_router.get("/users/")
async def get_users_total_fee(args: UserTotalFee = Depends(UserTotalFee)):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}}
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
        raise HTTPException(status_code=404, detail="Null response from database")
