from fastapi import APIRouter, Depends, HTTPException, Request
from schemas import UserTotalVolumeIn, UsersTotalVolumeIn, UsersTotalPureIn, PureLastNDaysIn
from database import get_database
from tools import to_gregorian, peek
from datetime import date, timedelta
from tokens import JWTBearer, get_sub
from serializers import volume_entity


volume_router = APIRouter(prefix='/volume', tags=['volume'])


@volume_router.get("/users/", dependencies=[Depends(JWTBearer())])
async def get_users_trades(request: Request, args: UsersTotalVolumeIn = Depends(UsersTotalVolumeIn)):
    # get user id
    marketer_id = get_sub(request)    
    db = get_database()

    # set collections
    customer_coll = db["customers"]
    trades_coll = db["trades"]
    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})
    marketer_dict = peek(query_result)

    # transform date from Gregorian to Jalali calendar
    from_gregorian_date = to_gregorian(args.from_date)
    to_gregorian_date = to_gregorian(args.to_date)

    
    query = {"Referer": {"$regex": marketer_dict.get("FirstName")}}

    fields = {"PAMCode": 1}

    records = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)

    trade_codes = []

    for record in records:
        trade_codes.append(record["PAMCode"])

    golden_pipeline = [
        {
            "$match": {"$and": [
                {"TradeCode": {"$in": trade_codes}},
                {"TradeDate": {"$gte": from_gregorian_date}},
                {"TradeDate": {"$lte": to_gregorian_date}}
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
                "TradeCode": "$_id",
                "TotalVolume": 1
            }
        },
        {
            "$limit": args.page_size
        },
        {
            "$skip": args.page_index
        }
    ]

    response = trades_coll.aggregate(pipeline=golden_pipeline)

    return { "Results": list(response), "TotalRecords": ""}


@volume_router.get("/user/", dependencies=[Depends(JWTBearer())])
async def get_user_total_trades(request: Request, args: UserTotalVolumeIn = Depends(UserTotalVolumeIn)):
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
    trade_codes = peek(customers_records)
    print(trade_codes)

    if not trade_codes:
        raise HTTPException(status_code=404, detail="Customer Not Found")
    else:

        # transform date from Gregorian to Jalali calendar
        gregorian_date = to_gregorian(args.from_date)

        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"TradeCode": args.trade_code},
                        {"TradeDate": {"$gte": gregorian_date}}
                        ]
                    }
                },
            {
                "$project": {
                    "Price": 1,
                    "Volume": 1,
                    "total": {"$multiply": ["$Price", "$Volume"]},
                }
            },
            {"$group": {"_id": "$id", "TotalVolume": {"$sum": "$total"}}},
        ]

        aggre_result = trades_coll.aggregate(pipeline=pipeline)

        volume_dict = next(aggre_result, {"TotalVolume": 0})

        return volume_entity(volume_dict)


@volume_router.get("/pure", dependencies=[Depends(JWTBearer())])
def get_users_total_trades(request: Request, args: UsersTotalPureIn = Depends(UsersTotalPureIn)):
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
        {"Referer": {"$regex": marketer_dict.get("FirstName")}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    from_gregorian_date = to_gregorian(args.from_date)

    to_gregorian_date = to_gregorian(args.to_date)

    buy_pipeline = [ 
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gte": from_gregorian_date}},
                    {"TradeDate": {"$lte": to_gregorian_date}},
                    {"TradeType": 1}
                    ]
                }
            },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total" : {"$multiply": ["$Price", "$Volume"]},
                "TotalCommission": 1,
                "Buy": {
                    "$add": [
                        "$TotalCommission",
                        {"$multiply": ["$Price", "$Volume"]}
                        ]
                    }
            }
        },
        {
            "$group": {
                "_id": "$id", 
                # "TotalVolume": {
                    # "$sum": "$Total"
                    # },
                # "TotCommissions": {
                    # "$sum": "$TotalCommission"
                # },
                "TotalBuy": {
                    "$sum": "$Buy"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalBuy": 1
            }
        }
    ]

    # sell
    sell_pipeline = [ 
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gte": from_gregorian_date}},
                    {"TradeDate": {"$lte": to_gregorian_date}},
                    {"TradeType": 2}
                    ]
                }
            },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total" : {"$multiply": ["$Price", "$Volume"]},
                "TotalCommission": 1,
                "Sell": {
                    "$subtract": [
                        {"$multiply": ["$Price", "$Volume"]},
                        "$TotalCommission"
                        ]
                    }
            }
        },
        {
            "$group": {
                "_id": "$id", 
                # "TotalVolume": {
                    # "$sum": "$Total"
                    # },
                # "TotCommissions": {
                    # "$sum": "$TotalCommission"
                # },
                "TotalSell": {
                    "$sum": "$Sell"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalSell": 1
            }
        }
    ]

    buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(trades_coll.aggregate(pipeline=sell_pipeline))

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        total_volume = total_sell + total_buy
        return { "TotalPureVolume": total_volume }
    else:
        return { "TotalPureVolume": 0 }


@volume_router.get("/pure_last_n_days", dependencies=[Depends(JWTBearer())])
def pure_last_n_day(request: Request, args: PureLastNDaysIn = Depends(PureLastNDaysIn)):
    # get user id
    marketer_id = get_sub(request) 
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]
    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    # Get current date
    from_date = date.today() - timedelta(days=args.last_n_days)

    from_date = from_date.strftime("%Y-%m-%d")
    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": marketer_dict.get("FirstName")}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    buy_pipeline = [ 
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gte": from_date}},
                    {"TradeType": 1}
                    ]
                }
            },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total" : {"$multiply": ["$Price", "$Volume"]},
                "TotalCommission": 1,
                "Buy": {
                    "$add": [
                        "$TotalCommission",
                        {"$multiply": ["$Price", "$Volume"]}
                        ]
                    }
            }
        },
        {
            "$group": {
                "_id": "$id", 
                # "TotalVolume": {
                    # "$sum": "$Total"
                    # },
                # "TotCommissions": {
                    # "$sum": "$TotalCommission"
                # },
                "TotalBuy": {
                    "$sum": "$Buy"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalBuy": 1
            }
        }
    ]

    # sell
    sell_pipeline = [ 
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gte": from_date}},
                    {"TradeType": 2}
                    ]
                }
            },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total" : {"$multiply": ["$Price", "$Volume"]},
                "TotalCommission": 1,
                "Sell": {
                    "$subtract": [
                        {"$multiply": ["$Price", "$Volume"]},
                        "$TotalCommission"
                        ]
                    }
            }
        },
        {
            "$group": {
                "_id": "$id", 
                # "TotalVolume": {
                    # "$sum": "$Total"
                    # },
                # "TotCommissions": {
                    # "$sum": "$TotalCommission"
                # },
                "TotalSell": {
                    "$sum": "$Sell"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalSell": 1
            }
        }
    ]

    buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(trades_coll.aggregate(pipeline=sell_pipeline))

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        total_volume = total_sell + total_buy
        return { "TotalPureVolume": total_volume }
    else:
        return { "TotalPureVolume": 0 }
