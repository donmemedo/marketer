from fastapi import APIRouter, Depends, HTTPException
from schemas import UserTotalVolumeIn, UsersTotalVolumeIn, UsersTotalPureIn, PureLastNDaysIn
from database import get_database
from tools import to_gregorian, remove_id, peek
from datetime import date, timedelta


volume_router = APIRouter(prefix='/volume', tags=['volume'])


@volume_router.get("/users/")
async def get_users_trades(args: UsersTotalVolumeIn = Depends(UsersTotalVolumeIn)):

    db = get_database()

    # set collections
    customer_coll = db["customers"]
    trades_coll = db["trades"]

    # transform date from Gregorian to Jalali calendar
    from_gregorian_date = to_gregorian(args.from_date)
    to_gregorian_date = to_gregorian(args.to_date)

    query = {"Referer": {"$regex": args.marketer_name}}

    fields = {"PAMCode": 1}

    records = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)

    total_records = customer_coll.count_documents(query)

    trade_codes = []

    for record in records:
        trade_codes.append(record["PAMCode"])

    response_list = []

    for trade_code in trade_codes:
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"TradeCode": trade_code}, 
                        {"TradeDate": {"$gte": from_gregorian_date}},
                        {"TradeDate": {"$lte": to_gregorian_date}}
                        ]
                    }
                },
            {
                "$project": {
                    "TradeCode": 1,
                    "Price": 1,
                    "Volume": 1,
                    "total": {"$multiply": ["$Price", "$Volume"]},
                }
            },
            {
                "$group": {
                    "_id": "$id",
                    "TradeCode": {"$first": "$TradeCode"},
                    "TotalVolume": {"$sum": "$total"},
                }
            },
        ]
        aggregate = trades_coll.aggregate(pipeline=pipeline)

        records = [r for r in aggregate]
        remove_id(records)

        if not records:
            response_list.append({"TradeCode": trade_code, "TotalVolume": 0})
        else:
            response_list.append(*records)

    return { "Results": response_list, "TotalRecords": total_records}


@volume_router.get("/user/")
async def get_user_total_trades(args: UserTotalVolumeIn = Depends(UserTotalVolumeIn)):
    db = get_database()
    trades_coll = db["trades"]

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
    aggregate = trades_coll.aggregate(pipeline=pipeline)

    records = [r for r in aggregate]
    remove_id(records)


    return records


@volume_router.get("/pure")
def get_users_total_trades(args: UsersTotalPureIn = Depends(UsersTotalPureIn)):
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
        raise HTTPException(status_code=404, detail="Null response from database")


@volume_router.get("/pure_last_n_days")
def pure_last_n_day(args: PureLastNDaysIn = Depends(PureLastNDaysIn)):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Get current date
    from_date = date.today() - timedelta(days=args.last_n_days)

    from_date = from_date.strftime("%Y-%m-%d")
    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}}
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
        raise HTTPException(status_code=404, detail="Null response from database")
