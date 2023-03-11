"""_summary_

Returns:
    _type_: _description_
"""
from fastapi import APIRouter, Depends, Request
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
# from tools import peek
from schemas import SubUserIn, SubUserOut, MarketerOut, CostIn, SubCostIn
from database import get_database
from tokens import JWTBearer, get_sub
from tools import to_gregorian_, peek
from datetime import datetime, timedelta
sub_user_router = APIRouter(prefix='/subuser', tags=['Sub User'])


@sub_user_router.get("/list/", dependencies=[Depends(JWTBearer())], response_model=Page[MarketerOut])
async def search_marketer_user(request: Request):
    """Gets List of ALL Marketers

    Args:
        request (Request): _description_

    Returns:
        _type_: MarketerOut
    """
    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()
    customer_coll = brokerage["customers"]
    marketers_coll = brokerage["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})
    marketer_dict = peek(query_result)
    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")

    # return paginate(customer_coll, {"Referer": marketer_fullname}, sort=[("RegisterDate", -1)])
    return paginate(marketers_coll,sort=[("CreateDate", -1)])


@sub_user_router.get("/profile/", dependencies=[Depends(JWTBearer())], response_model=Page[SubUserOut])
async def get_user_profile(request: Request, args: SubUserIn = Depends(SubUserIn)):
    """Gets List of Users of a Marketer and can search them

    Args:
        request (Request): _description_
        args (UserIn, optional): _description_. Defaults to Depends(UserIn).

    Returns:
        _type_: _description_
    """
    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()

    customer_coll = brokerage["customers"]
    marketers_coll = brokerage["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")

    query = {"$and": [
        {"Referer": marketer_fullname},
        {"FirstName": {"$regex": args.first_name}},
        {"LastName": {"$regex": args.last_name}}
        ]
    }
    print(query)
    return paginate(customer_coll, query, sort=[("RegisterDate", -1)])

@sub_user_router.get("/search/", dependencies=[Depends(JWTBearer())], response_model=Page[SubUserOut])
async def search_user_profile(request: Request, args: SubUserIn = Depends(SubUserIn)):
    """_summary_

    Args:
        request (Request): _description_
        args (UserIn, optional): _description_. Defaults to Depends(UserIn).

    Returns:
        _type_: _description_
    """
    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()

    customer_coll = brokerage["customers"]
    marketers_coll = brokerage["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")

    # query = {"$and": [
    #     {"Referer": marketer_fullname},
    #     {"FirstName": {"$regex": args.first_name}},
    #     {"LastName": {"$regex": args.last_name}}
    #     ]
    # }
    if args.username:

        filter = {
            'Referer': {
                '$regex': marketer_fullname
            },
            'FirstName': {
                '$regex': args.first_name
            },
            'LastName': {
                '$regex': args.last_name
            },
            'RegisterDate': {
                '$regex': args.register_date
            },
            'Phone': {
                '$regex': args.phone
            },
            'Mobile': {
                '$regex': args.mobile
            },
            'ID': {
                '$regex': args.user_id
            },
            'Username': {
                '$regex': args.username
            }
        }
    else:
        filter = {
            'Referer': {
                '$regex': marketer_fullname
            },
            'FirstName': {
                '$regex': args.first_name
            },
            'LastName': {
                '$regex': args.last_name
            },
            'RegisterDate': {
                '$regex': args.register_date
            },
            'Phone': {
                '$regex': args.phone
            },
            'Mobile': {
                '$regex': args.mobile
            },
            'ID': {
                '$regex': args.user_id
            }
        }

    sort = list({
                    'BirthDate': -1
                }.items())
    return paginate(customer_coll, filter, sort=[("RegisterDate", -1)])


@sub_user_router.get("/subuser/cost/", dependencies=[Depends(JWTBearer())])
async def call_subuser_cost(request: Request, args: SubCostIn = Depends(SubCostIn)):
    """_summary_

    Args:
        request (Request): _description_
        args (CostIn, optional): _description_. Defaults to Depends(CostIn).

    Returns:
        _type_: _description_
    """

    # get user id
    marketer_id = get_sub(request)
    brokerage = get_database()
    customers_coll = brokerage["customers"]
    trades_coll = brokerage["trades"]
    #ToDo: Because of having username isn't optional so it will have been changed to IDP or username
    query = {
        # 'Referer': {
        #     '$regex': marketer_fullname
        # },
        'FirstName': {
            '$regex': args.first_name
        },
        'LastName': {
            '$regex': args.last_name
        },
        'Phone': {
            '$regex': args.phone
        },
        'Mobile': {
            '$regex': args.mobile
        },
        'ID': {
            '$regex': args.user_id
        },
        'Username': {
            '$regex': args.username
        }
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
                "Total": {"$multiply": ["$Price", "$Volume"]},
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
                "Total": {"$multiply": ["$Price", "$Volume"]},
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
    subuser_total = {
        "TotalPureVolume": 0,
        "TotalFee": 0
    }

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        subuser_total["TotalPureVolume"] = total_sell + total_buy
        subuser_total["TotalFee"] = \
            sell_agg_result.get("TotalFee") + buy_agg_result.get("TotalFee")
    # tpv = subuser_total.get("TotalPureVolume")
    # pdf_maker(shobe='تهران', name='عباس خواجه زاده', doreh=args.to_date, total_fee=marketer_total.get("TotalFee"),
    #           pure_fee=pure_fee, marketer_fee=marketer_fee, tax=tax, colat2=two_months_ago_coll, colat=collateral,
    #           mandeh='0', pardakhti=final_fee + float(two_months_ago_coll), date=jd.now().strftime('%C'))
    return {
        "TotalBuy": total_buy,
        "TotalSell": total_sell,
        "TotalPureVolume": total_sell + total_buy,
        "TotalFee": subuser_total.get("TotalFee")
    }


add_pagination(sub_user_router)


def buy_pipe(trade_codes,from_gregorian_date,to_gregorian_date):
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
                "Total": {"$multiply": ["$Price", "$Volume"]},
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
    return buy_pipeline


def sell_pipe(trade_codes,from_gregorian_date,to_gregorian_date):
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
                "Total": {"$multiply": ["$Price", "$Volume"]},
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
    return sell_pipeline
