from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from schemas import UserTotalIn, MarketerTotalIn, UsersListIn, ResponseOut
from database import get_database
from tools import peek, to_gregorian_, get_marketer_name
from tokens import JWTBearer, get_sub
from khayyam import JalaliDatetime


volume_and_fee_router = APIRouter(prefix='/volume-and-fee', tags=['Volume and Fee'])


@volume_and_fee_router.get("/user-total/", dependencies=[Depends(JWTBearer())], response_model=None)
async def get_user_total_trades(request: Request, args: UserTotalIn = Depends(UserTotalIn)):
    db = get_database()

    # transform date from Gregorian to Jalali calendar
    # from_gregorian_date = to_gregorian_(args.from_date)
    from_gregorian_date = datetime.strptime(args.from_date, "%Y-%m-%d")
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(days=1)
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

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

    buy_agg_result = peek(db.trades.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(db.trades.aggregate(pipeline=sell_pipeline))


    buy_dict = {
        "vol": 0,
        "fee": 0
    }

    sell_dict = {
        "vol": 0,
        "fee": 0
    }

    if buy_agg_result:
        buy_dict['vol'] = buy_agg_result.get("TotalBuy")
        buy_dict['fee'] = buy_agg_result.get("TotalFee")

    if sell_agg_result:
        sell_dict['vol'] = sell_agg_result.get("TotalSell")
        sell_dict['fee'] = sell_agg_result.get("TotalFee")

    return ResponseOut(
        result={
        "TotalPureVolume": buy_dict.get("vol") + sell_dict.get("vol"),
        "TotalFee": buy_dict.get("fee") + sell_dict.get("fee")
        }, 
        timeGenerated=JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
        error=""
        )


@volume_and_fee_router.get("/marketer-total", dependencies=[Depends(JWTBearer())], response_model=None)
def get_marketer_total_trades(request: Request, args: MarketerTotalIn = Depends(MarketerTotalIn)):

    # get marketer id
    marketer_id = get_sub(request)    
    db = get_database()

    # check if marketer exists and return his name
    query_result = db.marketers.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")
    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": marketer_fullname}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = db.customers.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    from_gregorian_date = to_gregorian_(args.from_date)
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(days=1)
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

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

    buy_agg_result = peek(db.trades.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(db.trades.aggregate(pipeline=sell_pipeline))

    buy_dict = {
        "vol": 0,
        "fee": 0
    }

    sell_dict = {
        "vol": 0,
        "fee": 0
    }

    if buy_agg_result:
        buy_dict['vol'] = buy_agg_result.get("TotalBuy")
        buy_dict['fee'] = buy_agg_result.get("TotalFee")

    if sell_agg_result:
        sell_dict['vol'] = sell_agg_result.get("TotalSell")
        sell_dict['fee'] = sell_agg_result.get("TotalFee")

    # return {
        # "TotalPureVolume": buy_dict.get("vol") + sell_dict.get("vol"),
        # "TotalFee": buy_dict.get("fee") + sell_dict.get("fee")
    # }

    return ResponseOut(
        result={
        "TotalPureVolume": buy_dict.get("vol") + sell_dict.get("vol"),
        "TotalFee": buy_dict.get("fee") + sell_dict.get("fee")
        }, 
        timeGenerated=JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
        error=""
        )


@volume_and_fee_router.get("/users-total", dependencies=[Depends(JWTBearer())])
def users_list_by_volume(request: Request, args: UsersListIn = Depends(UsersListIn)):
    # get user id
    marketer_id = get_sub(request)
    db = get_database()

    customers_coll = db.customers
    trades_coll = db.trades
    marketers_coll = db.marketers

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = get_marketer_name(marketer_dict)

    from_gregorian_date = to_gregorian_(args.from_date)
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(days=1)
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

    # get all customers' TradeCodes
    customers_records = customers_coll.find({"Referer":  marketer_fullname}, 
                                            {"PAMCode": 1}
                                            )

    trade_codes = [c.get('PAMCode') for c in customers_records]

    if args.user_type.value == "active":
        pipeline = [ 
            {
                "$match": {
                    "$and": [
                        {"TradeCode": {"$in": trade_codes}}, 
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
                    "TradeCode": 1,
                    "Commission": {
                        "$cond": { 
                            "if": {"$eq": ["$TradeType", 1]}, 
                            "then": {
                                "$add": [
                                    "$TotalCommission",
                                    {"$multiply": ["$Price", "$Volume"]}
                                ]
                            }, 
                            "else": {
                                "$subtract": [
                                    {"$multiply": ["$Price", "$Volume"]},
                                    "$TotalCommission"
                                ]
                            }
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": "$TradeCode",
                    "TotalFee": {
                     "$sum": "$TradeItemBroker"
                    },
                    "TotalPureVolume": {"$sum": "$Commission"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "TradeCode": "$_id",
                    "TotalPureVolume": 1,
                    "TotalFee": 1
                }
            },
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "TradeCode",
                    "foreignField": "PAMCode",
                    "as": "UserProfile"
                }
            },
            {
                "$unwind": "$UserProfile"
            },
            {
                "$project": {
                    "TradeCode": 1,
                    "TotalFee": 1,
                    "TotalPureVolume": 1,
                    "FirstName": "$UserProfile.FirstName",
                    "LastName": "$UserProfile.LastName",
                    "Username": "$UserProfile.Username",
                    "Mobile": "$UserProfile.Mobile",
                    "RegisterDate": "$UserProfile.RegisterDate",
                    "BankAccountNumber": "$UserProfile.BankAccountNumber",
                }
            },
            {
                "$sort": {
                    args.sort_by.value: args.sort_order.value
                }
            },
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "items": [
                        {"$skip": (args.page - 1) * args.size }, 
                        {"$limit": args.size }
                    ]
                }
            },
            {
                "$unwind": "$metadata" 
            },
            {
                "$project": {
                    "total": "$metadata.total",
                    "items": 1,
                }
            }
        ]

        aggr_result = trades_coll.aggregate(pipeline=pipeline)
    
        active_dict = next(aggr_result, None)

        if active_dict is None:
            return {}

        active_dict["page"] = args.page
        active_dict["size"] = args.size
        active_dict["pages"] = - ( active_dict.get("total") // - args.size )

        return active_dict

    elif args.user_type.value == "inactive":
        active_users_pipeline = [ 
            {
                "$match":
                         {"$and": [
                            {"TradeCode": {"$in": trade_codes}}, 
                            {"TradeDate": {"$gte": from_gregorian_date}},
                            {"TradeDate": {"$lte": to_gregorian_date}} 
                        ]
                    }
                }, 
            {
                "$group": {
                    "_id": "$TradeCode"
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "TradeCode": "$_id"
                }
            }
        ]

        active_users_res = trades_coll.aggregate(pipeline=active_users_pipeline)
        active_users_set = set(i.get("TradeCode") for i in active_users_res)

        # check wether it is empty or not
        inactive_uesrs_set = set(trade_codes) - active_users_set

        inactive_users_pipline = [
            {
                "$match": {
                    "PAMCode": {"$in": list(inactive_uesrs_set)}
                }
            },
                {
                "$project": {
                    "_id": 0,
                    "TradeCode": 1,
                    "FirstName": 1,
                    "LastName": 1,
                    "Username": 1,
                    "Mobile": 1,
                    "RegisterDate": 1,
                    "BankAccountNumber": 1,
                }
            },
                {
                "$sort": {
                    args.sort_by.value: args.sort_order.value
                }
            },
                   {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "items": [
                        {"$skip": (args.page - 1) * args.size }, 
                        {"$limit": args.size }
                    ]
                }
            },
            {
                "$unwind": "$metadata" 
            },
            {
                "$project": {
                    "total": "$metadata.total",
                    "items": 1,
                }
            }
        ]

        inactives_result = customers_coll.aggregate(pipeline=inactive_users_pipline)
        inactives_dict = next(inactives_result, None)
        inactives_dict["page"] = args.page
        inactives_dict["size"] = args.size
        inactives_dict["pages"] = - ( inactives_dict.get("total") // - args.size )

        return inactives_dict
    else:
        return {}


