from fastapi import Depends, APIRouter, Request
from serializers import marketer_entity
from database import get_database
from tokens import JWTBearer, get_sub
from schemas import CostIn, MarketerInvitationOut, MarketerInvitationIn, MarketerIdpIdIn
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from tools import to_gregorian, peek


plan_router = APIRouter(prefix='/marketer', tags=['Marketer'])


@plan_router.get("/profile/", dependencies=[Depends(JWTBearer())])
async def get_marketer_profile(request: Request):
    marketer_id = get_sub(request)
    db = get_database()

    marketers_coll = db["marketers"]

    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})

    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict) 


@plan_router.get("/cost/", dependencies=[Depends(JWTBearer())])
async def cal_marketer_cost(request: Request, args: CostIn = Depends(CostIn)):

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
    marketer_total = {
        "TotalPureVolume": 0,
        "TotalFee": 0
    }

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        marketer_total["TotalPureVolume"] = total_sell + total_buy
        marketer_total["TotalFee"] = sell_agg_result.get("TotalFee") + buy_agg_result.get("TotalFee")

    # find marketer's plan
    marketer_plans = {
        "payeh": {"start": 0, "end": 3000000000, "marketer_share": .05},
        "morvarid": {"start": 3000000000, "end": 5000000000, "marketer_share": .1},
        "firouzeh": {"start": 5000000000, "end": 10000000000, "marketer_share": .15},
        "aghigh": {"start": 10000000000, "end": 15000000000, "marketer_share": .2},
        "yaghout": {"start": 15000000000, "end": 20000000000, "marketer_share": .25},
        "zomorod": {"start": 20000000000, "end": 25000000000, "marketer_share": .3},
        "tala": {"start": 25000000000, "end": 40000000000, "marketer_share": .35},
        "almas": {"start": 40000000000, "marketer_share": .4}
    }

    x1 = marketer_total.get("TotalFee") * .65
    x2 = 0
    if marketer_plans["payeh"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["payeh"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["morvarid"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["morvarid"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["firouzeh"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["firouzeh"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["aghigh"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["aghigh"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["yaghout"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["yaghout"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["zomorod"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["zomorod"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["tala"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["tala"]["end"]:
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["almas"]["start"] <= marketer_total.get("TotalPureVolume"):
        x2 = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]

    x3 = x1 + x2

    if args.salary != 0:
        x3 -= args.salary

        if args.insurance != 0:
            x3 -= args.insurance

    if args.tax != 0:
        x3 -= args.tax

    if args.collateral !=0:
        x3 -= args.tax

    return {
        "PureFee": x1, 
        "FinalFee": x3
        } 


@plan_router.put("/set-invitation-link")
async def set_marketer_invitation_link(args: MarketerInvitationIn = Depends(MarketerInvitationIn)):
    db = get_database()
    marketers_coll = db["marketers"]

    filter = {"Id": args.id}
    update = {"$set": {"InvitationLink": args.invitation_link}}

    marketers_coll.update_one(filter, update)
    query_result = marketers_coll.find(filter)
    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict)


@plan_router.put("/set-idp-id")
async def set_marketer_idpid(args: MarketerIdpIdIn = Depends(MarketerIdpIdIn)):
    db = get_database()
    marketers_coll = db["marketers"]

    filter = {"Id": args.id}
    update = {"$set": {"IdpId": args.idpid}}

    marketers_coll.update_one(filter, update)
    query_result = marketers_coll.find(filter)
    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict)


@plan_router.get("/list-all-marketers/", response_model=Page[MarketerInvitationOut])
async def list_all_marketers():
    db = get_database()
    marketers_coll = db["marketers"]

    return paginate(marketers_coll, {})


add_pagination(plan_router) 