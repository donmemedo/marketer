from fastapi import APIRouter, Depends, Request
from schemas import UserTotalVolumeIn, UsersTotalPureIn
from database import get_database
from tools import to_gregorian, peek
from tokens import JWTBearer, get_sub


volume_and_fee_router = APIRouter(prefix='/volume-and-fee', tags=['Volume and Fee'])


@volume_and_fee_router.get("/user-total/", dependencies=[Depends(JWTBearer())])
async def get_user_total_trades(request: Request, args: UserTotalVolumeIn = Depends(UserTotalVolumeIn)):
    db = get_database()

    trades_coll = db["trades"]

    # transform date from Gregorian to Jalali calendar
    from_gregorian_date = to_gregorian(args.from_date)
    to_gregorian_date = to_gregorian(args.to_date)

    buy_pipeline = [ 
        {
            "$match": {
                "$and": [
                    {"TradeCode": args.trade_code }, 
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
                "TradeItemBroker": 1,
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
                "TotalFee": {
                    "$sum": "$TradeItemBroker"
                },
                "TotalBuy": {
                    "$sum": "$Buy"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalBuy": 1,
                "TotalFee": 1
            }
        }
    ]

    sell_pipeline = [ 
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
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total" : {"$multiply": ["$Price", "$Volume"]},
                "TotalCommission": 1,
                "TradeItemBroker": 1,
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
                "TotalFee": {
                 "$sum": "$TradeItemBroker"
                },
                "TotalSell": {
                    "$sum": "$Sell"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalSell": 1,
                "TotalFee": 1
            }
        }
    ]

    buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(trades_coll.aggregate(pipeline=sell_pipeline))

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        total_volume = total_sell + total_buy
        total_fee = sell_agg_result.get("TotalFee") + buy_agg_result.get("TotalFee")

        return { 
            "TotalPureVolume": total_volume, 
            "TotalFee": total_fee 
            }
    else:
        return { "TotalPureVolume": 0 }


@volume_and_fee_router.get("/marketer-total", dependencies=[Depends(JWTBearer())])
def get_marketer_total_trades(request: Request, args: UsersTotalPureIn = Depends(UsersTotalPureIn)):
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
                "TradeItemBroker": 1,
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
                "TotalFee": {
                    "$sum": "$TradeItemBroker"
                },
                "TotalBuy": {
                    "$sum": "$Buy"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalBuy": 1,
                "TotalFee": 1
            }
        }
    ]

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
                "TradeItemBroker": 1,
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
                "TotalFee": {
                 "$sum": "$TradeItemBroker"
                },
                "TotalSell": {
                    "$sum": "$Sell"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "TotalSell": 1,
                "TotalFee": 1
            }
        }
    ]

    buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(trades_coll.aggregate(pipeline=sell_pipeline))

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        total_volume = total_sell + total_buy
        total_fee = sell_agg_result.get("TotalFee") + buy_agg_result.get("TotalFee")
        return { 
            "TotalPureVolume": total_volume, 
            "TotalFee": total_fee 
            }
    else:
        return { "TotalPureVolume": 0 }


@volume_and_fee_router.get("/users-list-by-volume", dependencies=[Depends(JWTBearer())])
def users_list_by_volume(request: Request):
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

    print(len(trade_codes))

    # buy_pipeline = [ 
        # {
            # "$match": {
                # "$and": [
                    # {"TradeCode": {"$in": trade_codes}},
                    # {"TradeType": 1}
                    # ]
                # }
            # },
        # {
            # "$project": {
                # "Price": 1,
                # "Volume": 1,
                # "Total" : {"$multiply": ["$Price", "$Volume"]},
                # "TotalCommission": 1,
                # "TradeItemBroker": 1,
                # "Buy": {
                    # "$add": [
                        # "$TotalCommission",
                        # {"$multiply": ["$Price", "$Volume"]}
                        # ]
                    # }
            # }
        # },
        # {
            # "$group": {
                # "_id": "$id", 
                # "TotalFee": {
                    # "$sum": "$TradeItemBroker"
                # },
                # "TotalBuy": {
                    # "$sum": "$Buy"
                # }
            # }
        # },
        # {
            # "$project": {
                # "_id": 0,
                # "TotalBuy": 1,
                # "TotalFee": 1
            # }
        # }
    # ]
# 
    # sell_pipeline = [ 
        # {
            # "$match": {
                # "$and": [
                    # {"TradeCode": {"$in": trade_codes}}, 
                    # ]
                # }
            # },
        # {
            # "$project": {
                # "Price": 1,
                # "Volume": 1,
                # "Total" : {"$multiply": ["$Price", "$Volume"]},
                # "TotalCommission": 1,
                # "TradeItemBroker": 1,
                # "TradeCode": 1,
                # "Sell": {
                    # "$subtract": [
                        # {"$multiply": ["$Price", "$Volume"]},
                        # "$TotalCommission"
                        # ]
                    # },
                # "Temp": {
                    # "$cond": { "if": {"TradeType": 1}, "then": 11, "else": 22}
                # }
            # }
        # },
        # {
            # "$group": {
                # "_id": "$TradeCode",
                # "TotalFee": {
                #  "$sum": "$TradeItemBroker"
                # },
                # "SellTotal": 
            # }
        # }
    # ]
# 
    # buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    # sell_agg_result = list(trades_coll.aggregate(pipeline=sell_pipeline))
# 
    # print(sell_agg_result)


    return 
    # if buy_agg_result and sell_agg_result:
        # total_buy = buy_agg_result.get("TotalBuy")
        # total_sell = sell_agg_result.get("TotalSell")
        # total_volume = total_sell + total_buy
        # total_fee = sell_agg_result.get("TotalFee") + buy_agg_result.get("TotalFee")
        # return { 
            # "TotalPureVolume": total_volume, 
            # "TotalFee": total_fee 
            # }
    # else:
        # return { "TotalPureVolume": 0 }
