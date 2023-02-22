"""_summary_

Returns:
    _type_: _description_
"""
from datetime import timedelta, datetime
from fastapi import Depends, APIRouter, Request
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from serializers import marketer_entity
from database import get_database
from tokens import JWTBearer, get_sub
from schemas import CostIn, MarketerInvitationOut, MarketerInvitationIn, MarketerIdpIdIn
from tools import to_gregorian_, peek

plan_router = APIRouter(prefix='/marketer', tags=['Marketer'])


@plan_router.get("/profile/", dependencies=[Depends(JWTBearer())])
async def get_marketer_profile(request: Request):
    """_summary_

    Args:
        request (Request): _description_

    Returns:
        _type_: _description_
    """
    marketer_id = get_sub(request)
    brokerage = get_database()
    marketers_coll = brokerage["marketers"]
    # check if marketer exists and return his name
    query_result = marketers_coll.find({"IdpId": marketer_id})
    marketer_dict = next(query_result, None)
    return marketer_entity(marketer_dict)


@plan_router.get("/cost/", dependencies=[Depends(JWTBearer())])
async def cal_marketer_cost(request: Request, args: CostIn = Depends(CostIn)):
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
    marketers_coll = brokerage["marketers"]

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
    marketer_total = {
        "TotalPureVolume": 0,
        "TotalFee": 0
    }

    if buy_agg_result and sell_agg_result:
        total_buy = buy_agg_result.get("TotalBuy")
        total_sell = sell_agg_result.get("TotalSell")
        marketer_total["TotalPureVolume"] = total_sell + total_buy
        marketer_total["TotalFee"] = \
            sell_agg_result.get("TotalFee") + buy_agg_result.get("TotalFee")

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

    # pure_fee = marketer_total.get("TotalFee") * .65
    pure_fee = marketer_total.get("TotalFee") * .65
    marketer_fee = 0
    if marketer_plans["payeh"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["payeh"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["payeh"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["payeh"]["marketer_share"]
    elif marketer_plans["morvarid"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["morvarid"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["morvarid"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["morvarid"]["marketer_share"]
    elif marketer_plans["firouzeh"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["firouzeh"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["firouzeh"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["firouzeh"]["marketer_share"]
    elif marketer_plans["aghigh"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["aghigh"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["aghigh"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["aghigh"]["marketer_share"]
    elif marketer_plans["yaghout"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["yaghout"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["yaghout"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["yaghout"]["marketer_share"]
    elif marketer_plans["zomorod"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["zomorod"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["zomorod"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["zomorod"]["marketer_share"]
    elif marketer_plans["tala"]["start"] <= marketer_total.get("TotalPureVolume") < marketer_plans["tala"]["end"]:
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["tala"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["tala"]["marketer_share"]
    elif marketer_plans["almas"]["start"] <= marketer_total.get("TotalPureVolume"):
        # marketer_fee = marketer_total.get("TotalFee") * marketer_plans["almas"]["marketer_share"]
        marketer_fee = pure_fee * marketer_plans["almas"]["marketer_share"]

    # final_fee = pure_fee + marketer_fee
    final_fee = marketer_fee

    if args.salary != 0:
        final_fee -= args.salary
        if args.insurance != 0:
            final_fee -= args.insurance

    if args.tax != 0:
        # final_fee -= args.tax
        final_fee -= final_fee * args.tax

    if args.collateral != 0:
        # final_fee -= args.tax
        collateral = final_fee * args.collateral
        #ToDo: collateral will be paid 2 months later, so it must be saved in DB.
        final_fee -= collateral

    if args.tax == 0 and args.collateral == 0:
        # final_fee -= args.tax
        final_fee -= final_fee * 0.15

    return {
        "PureFee": pure_fee, 
        "FinalFee": final_fee
        }


@plan_router.put("/set-invitation-link")
async def set_marketer_invitation_link(args: MarketerInvitationIn = Depends(MarketerInvitationIn)):
    """_summary_

    Args:
        args (MarketerInvitationIn, optional):
         _description_. Defaults to Depends(MarketerInvitationIn).

    Returns:
        _type_: _description_
    """
    brokerage = get_database()
    marketers_coll = brokerage["marketers"]

    smil_filter = {"Id": args.id}
    update = {"$set": {"InvitationLink": args.invitation_link}}

    marketers_coll.update_one(smil_filter, update)
    query_result = marketers_coll.find(smil_filter)
    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict)


@plan_router.put("/set-idp-id")
async def set_marketer_idpid(args: MarketerIdpIdIn = Depends(MarketerIdpIdIn)):
    """_summary_

    Args:
        args (MarketerIdpIdIn, optional): _description_. Defaults to Depends(MarketerIdpIdIn).

    Returns:
        _type_: _description_
    """
    brokerage = get_database()
    marketers_coll = brokerage["marketers"]

    smi_filter = {"Id": args.id}
    update = {"$set": {"IdpId": args.idpid}}

    marketers_coll.update_one(smi_filter, update)
    query_result = marketers_coll.find(smi_filter)
    marketer_dict = next(query_result, None)

    return marketer_entity(marketer_dict)


@plan_router.get("/list-all-marketers/", response_model=Page[MarketerInvitationOut])
async def list_all_marketers():
    """_summary_

    Returns:
        _type_: _description_
    """
    brokerage = get_database()
    marketers_coll = brokerage["marketers"]

    return paginate(marketers_coll, {})


add_pagination(plan_router)
