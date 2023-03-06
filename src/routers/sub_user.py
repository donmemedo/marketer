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
    """_summary_

    Args:
        request (Request): _description_

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

    # return paginate(customer_coll, {"Referer": marketer_fullname}, sort=[("RegisterDate", -1)])
    return paginate(marketers_coll,sort=[("CreateDate", -1)])


@sub_user_router.get("/profile/", dependencies=[Depends(JWTBearer())], response_model=Page[SubUserOut])
async def get_user_profile(request: Request, args: SubUserIn = Depends(SubUserIn)):
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

    query = {"$and": [
        {"Referer": marketer_fullname},
        {"FirstName": {"$regex": args.first_name}},
        {"LastName": {"$regex": args.last_name}}
        ]
    }

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
    sort = list({
                    'BirthDate': -1
                }.items())

    # result = customer_coll.find(
    #     filter=filter,
    #     sort=sort
    # )
    # result = customer_coll.find(
    #     filter=filter
    # )
    # print(list(result))
    return paginate(customer_coll, filter, sort=[("BirthDate", -1)])


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
    # subuser_id = get_sub(request)
    marketer_id = get_sub(request)


    marketer_id = get_sub(request)
    brokerage = get_database()

    customer_coll = brokerage["customers"]
    marketers_coll = brokerage["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = peek(query_result)

    marketer_fullname = marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")




    brokerage = get_database()
    customers_coll = brokerage["customers"]
    trades_coll = brokerage["trades"]
    marketers_coll = brokerage["marketers"]
    factor_coll = brokerage["factor"]
    aaaaaa= marketer_dict.get("LastName")
    # check if marketer exists and return his name
    query_result = customers_coll.find({"Referer": {'$regex': marketer_dict.get("LastName")}})
    print(query_result)
    subuser_dict = peek(query_result)

    # Check if customer exist
    query = {"$and": [
        # {"FirstName": subuser_dict.get("FirstName")}
        {'FirstName':{'$regex':args.first_name}}
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
    #
    # # find marketer's plan
    # marketer_plans = {
    #     "payeh": {"start": 0, "end": 30000000000, "marketer_share": .05},
    #     "morvarid": {"start": 30000000000, "end": 50000000000, "marketer_share": .1},
    #     "firouzeh": {"start": 50000000000, "end": 100000000000, "marketer_share": .15},
    #     "aghigh": {"start": 100000000000, "end": 150000000000, "marketer_share": .2},
    #     "yaghout": {"start": 150000000000, "end": 200000000000, "marketer_share": .25},
    #     "zomorod": {"start": 200000000000, "end": 300000000000, "marketer_share": .3},
    #     "tala": {"start": 300000000000, "end": 400000000000, "marketer_share": .35},
    #     "almas": {"start": 400000000000, "marketer_share": .4}
    # }
    #
    # # pure_fee = marketer_total.get("TotalFee") * .65
    # pure_fee = marketer_total.get("TotalFee") * .65
    subuser_fee = 0
    tpv = subuser_total.get("TotalPureVolume")
    # if marketer_plans["payeh"]["start"] <= tpv < marketer_plans["payeh"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["payeh"]["marketer_share"]
    #     plan = "Payeh"
    # elif marketer_plans["morvarid"]["start"] <= tpv < marketer_plans["morvarid"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["morvarid"]["marketer_share"]
    #     plan = "Morvarid"
    # elif marketer_plans["firouzeh"]["start"] <= tpv < marketer_plans["firouzeh"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["firouzeh"]["marketer_share"]
    #     plan = "Firouzeh"
    # elif marketer_plans["aghigh"]["start"] <= tpv < marketer_plans["aghigh"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["aghigh"]["marketer_share"]
    #     plan = "Aghigh"
    # elif marketer_plans["yaghout"]["start"] <= tpv < marketer_plans["yaghout"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["yaghout"]["marketer_share"]
    #     plan = "Yaghout"
    # elif marketer_plans["zomorod"]["start"] <= tpv < marketer_plans["zomorod"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["zomorod"]["marketer_share"]
    #     plan = "Zomorod"
    # elif marketer_plans["tala"]["start"] <= tpv < marketer_plans["tala"]["end"]:
    #     marketer_fee = pure_fee * marketer_plans["tala"]["marketer_share"]
    #     plan = "Tala"
    # elif marketer_plans["almas"]["start"] <= tpv:
    #     marketer_fee = pure_fee * marketer_plans["almas"]["marketer_share"]
    #     plan = "Almas"

    # final_fee = pure_fee + marketer_fee
    # final_fee = subuser_fee
    # salary = 0
    # insurance = 0
    # if args.salary != 0:
    #     salary = args.salary * subuser_fee
    #     final_fee -= salary
    #     if args.insurance != 0:
    #         insurance = args.insurance * subuser_fee
    #         final_fee -= insurance
    #
    # if args.tax != 0:
    #     # final_fee -= args.tax
    #     tax = subuser_fee * args.tax
    #     final_fee -= tax
    #
    # if args.collateral != 0:
    #     # final_fee -= args.tax
    #     collateral = subuser_fee * args.collateral
    #     final_fee -= collateral
    # if args.tax == 0 and args.collateral == 0:
    #     # final_fee -= args.tax
    #     collateral = subuser_fee * 0.05
    #     tax = subuser_fee * 0.1
    #     final_fee -= final_fee * 0.15
    # two_months_ago_coll = 0

    try:
        factor_coll.insert_one(
            {"MarketerID": marketer_dict['IdpId'], "ThisMonth": jd.today().month,
             "ThisM_Collateral": collateral, "ThisM_FinalFee": final_fee,
             "LastM_Collateral": "0", "LastM_FinalFee": "0", "2LastM_Collateral": "0",
             "2LastM_FinalFee": "0"})
    except:
        # update database to this month and shift past months
        if jd.today().month > factor_coll.find_one(
                {"MarketerID": marketer_dict['IdpId']})["ThisMonth"]:
            this_month_coll = factor_coll.find_one(
                {"MarketerID": marketer_dict['IdpId']})["ThisM_Collateral"]
            one_month_ago_coll = factor_coll.find_one(
                {"MarketerID": marketer_dict['IdpId']})["LastM_Collateral"]
            this_month_fee = factor_coll.find_one(
                {"MarketerID": marketer_dict['IdpId']})["ThisM_FinalFee"]
            one_month_ago_fee = factor_coll.find_one(
                {"MarketerID": marketer_dict['IdpId']})["LastM_FinalFee"]
            two_months_ago_coll = factor_coll.find_one(
                {"MarketerID": marketer_dict['IdpId']})["2LastM_Collateral"]
            factor_coll.update_one(
                {"MarketerID": marketer_dict['IdpId']},
                {"$set":
                     {"ThisM_Collateral": collateral, "ThisM_FinalFee": final_fee,
                      "LastM_Collateral": this_month_coll, "LastM_FinalFee": this_month_fee,
                      "2LastM_Collateral": one_month_ago_coll, "2LastM_FinalFee": one_month_ago_fee}
                 }
            )
        elif args.to_date == str(jd.today().date()) and \
                args.from_date == str(jd.today().replace(day=1).date()):
            # just update datas of this month and dont shift past months
            factor_coll.update_one(
                {"MarketerID": marketer_dict['IdpId']},
                {"$set":
                     {"ThisM_Collateral": collateral, "ThisM_FinalFee": final_fee}
                 }
            )

    pdf_maker(shobe='تهران', name='عباس خواجه زاده', doreh=args.to_date, total_fee=marketer_total.get("TotalFee"),
              pure_fee=pure_fee, marketer_fee=marketer_fee, tax=tax, colat2=two_months_ago_coll, colat=collateral,
              mandeh='0', pardakhti=final_fee + float(two_months_ago_coll), date=jd.now().strftime('%C'))
    return {
        "TotalFee": marketer_total.get("TotalFee"),
        "PureFee": pure_fee,
        "MarketerFee": marketer_fee,
        "Plan": plan,
        "Tax": tax,
        "Collateral": collateral,
        "FinalFee": final_fee,
        "CollateralOfTwoMonthAgo": two_months_ago_coll,
        "Payment": final_fee + float(two_months_ago_coll)
    }


add_pagination(sub_user_router)
