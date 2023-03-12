from fastapi import APIRouter, Depends, Request
from schemas import UserTotalVolumeIn, UsersTotalPureIn, UsersListIn
from database import get_database
from tools import peek, to_gregorian_
from tokens import JWTBearer, get_sub
from datetime import datetime, timedelta


volume_and_fee_router = APIRouter(prefix='/volume-and-fee', tags=['Volume and Fee'])


@volume_and_fee_router.get("/user-total/", dependencies=[Depends(JWTBearer())])
async def get_user_total_trades(request: Request, args: UserTotalVolumeIn = Depends(UserTotalVolumeIn)):
    db = get_database()

    trades_coll = db["trades"]

    # transform date from Gregorian to Jalali calendar
    from_gregorian_date = to_gregorian_(args.from_date)
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

    buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(trades_coll.aggregate(pipeline=sell_pipeline))


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

    return {
        "TotalPureVolume": buy_dict.get("vol") + sell_dict.get("vol"),
        "TotalFee": buy_dict.get("fee") + sell_dict.get("fee")
    }


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

    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")
    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": marketer_fullname}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
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

    buy_agg_result = peek(trades_coll.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(trades_coll.aggregate(pipeline=sell_pipeline))

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

    return {
        "TotalPureVolume": buy_dict.get("vol") + sell_dict.get("vol"),
        "TotalFee": buy_dict.get("fee") + sell_dict.get("fee")
    }


@volume_and_fee_router.get("/users-total", dependencies=[Depends(JWTBearer())])
def users_list_by_volume(request: Request, args: UsersListIn = Depends(UsersListIn)):
    # get user id
    marketer_id = get_sub(request)    
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]
    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    if marketer_dict.get("FirstName") == "":
        marketer_fullname = marketer_dict.get("LastName")
    elif marketer_dict.get("LastName") == "":
        marketer_fullname = marketer_dict.get("FirstName")
    else:
        marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")


    from_gregorian_date = to_gregorian_(args.from_date)
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(days=1)
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

    # get all customers' TradeCodes
    query = {"$and": [
        {"Referer":  marketer_fullname }
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    pipeline = [ 
        {
            "$match": {
                    # "TradeCode": {"$in": trade_codes}
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
                "TotalPureVolume": 1,
                "RegisterDate": 1,
                "TradeCode": 1 
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
    
    aggre_dict = next(aggr_result, None)

    if aggre_dict is None:
        return {}

    aggre_dict["page"] = args.page
    aggre_dict["size"] = args.size
    aggre_dict["pages"] = - ( aggre_dict.get("total") // - args.size )

    return aggre_dict
