"""_summary_

Returns:
    _type_: _description_
"""
from datetime import timedelta, datetime
from khayyam import JalaliDatetime as jd
from fastapi import Depends, APIRouter, Request
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.pymongo import paginate
from serializers import marketer_entity
from database import get_database
from tokens import JWTBearer, get_sub
from schemas import CostIn, MarketerInvitationOut, MarketerInvitationIn, MarketerIdpIdIn
from tools import to_gregorian_, peek
# from ..pdf import pdf_maker
from src.pdf import pdf_maker
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
    factor_coll = brokerage["factor"]

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
        "payeh": {"start": 0, "end": 30000000000, "marketer_share": .05},
        "morvarid": {"start": 30000000000, "end": 50000000000, "marketer_share": .1},
        "firouzeh": {"start": 50000000000, "end": 100000000000, "marketer_share": .15},
        "aghigh": {"start": 100000000000, "end": 150000000000, "marketer_share": .2},
        "yaghout": {"start": 150000000000, "end": 200000000000, "marketer_share": .25},
        "zomorod": {"start": 200000000000, "end": 300000000000, "marketer_share": .3},
        "tala": {"start": 300000000000, "end": 400000000000, "marketer_share": .35},
        "almas": {"start": 400000000000, "marketer_share": .4}
    }

    # pure_fee = marketer_total.get("TotalFee") * .65
    pure_fee = marketer_total.get("TotalFee") * .65
    marketer_fee = 0
    tpv = marketer_total.get("TotalPureVolume")
    if marketer_plans["payeh"]["start"] <= tpv < marketer_plans["payeh"]["end"]:
        marketer_fee = pure_fee * marketer_plans["payeh"]["marketer_share"]
        plan = "Payeh"
    elif marketer_plans["morvarid"]["start"] <= tpv < marketer_plans["morvarid"]["end"]:
        marketer_fee = pure_fee * marketer_plans["morvarid"]["marketer_share"]
        plan = "Morvarid"
    elif marketer_plans["firouzeh"]["start"] <= tpv < marketer_plans["firouzeh"]["end"]:
        marketer_fee = pure_fee * marketer_plans["firouzeh"]["marketer_share"]
        plan = "Firouzeh"
    elif marketer_plans["aghigh"]["start"] <= tpv < marketer_plans["aghigh"]["end"]:
        marketer_fee = pure_fee * marketer_plans["aghigh"]["marketer_share"]
        plan = "Aghigh"
    elif marketer_plans["yaghout"]["start"] <= tpv < marketer_plans["yaghout"]["end"]:
        marketer_fee = pure_fee * marketer_plans["yaghout"]["marketer_share"]
        plan = "Yaghout"
    elif marketer_plans["zomorod"]["start"] <= tpv < marketer_plans["zomorod"]["end"]:
        marketer_fee = pure_fee * marketer_plans["zomorod"]["marketer_share"]
        plan = "Zomorod"
    elif marketer_plans["tala"]["start"] <= tpv < marketer_plans["tala"]["end"]:
        marketer_fee = pure_fee * marketer_plans["tala"]["marketer_share"]
        plan = "Tala"
    elif marketer_plans["almas"]["start"] <= tpv:
        marketer_fee = pure_fee * marketer_plans["almas"]["marketer_share"]
        plan = "Almas"

    # final_fee = pure_fee + marketer_fee
    final_fee = marketer_fee
    salary = 0
    insurance = 0
    if args.salary != 0:
        salary = args.salary * marketer_fee
        final_fee -= salary
        if args.insurance != 0:
            insurance = args.insurance * marketer_fee
            final_fee -= insurance

    if args.tax != 0:
        # final_fee -= args.tax
        tax = marketer_fee * args.tax
        final_fee -= tax

    if args.collateral != 0:
        # final_fee -= args.tax
        collateral = marketer_fee * args.collateral
        final_fee -= collateral
    if args.tax == 0 and args.collateral == 0:
        # final_fee -= args.tax
        collateral = marketer_fee * 0.05
        tax = marketer_fee * 0.1
        final_fee -= final_fee * 0.15
    two_months_ago_coll = 0
    
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
        elif args.to_date == str(jd.today().date()) and\
                args.from_date == str(jd.today().replace(day=1).date()):
            # just update datas of this month and dont shift past months
            factor_coll.update_one(
                {"MarketerID": marketer_dict['IdpId']},
                {"$set":
                     {"ThisM_Collateral": collateral, "ThisM_FinalFee": final_fee}
                 }
            )

    pdf_maker(shobe='تهران', name='عباس خواجه زاده', doreh=args.to_date, total_fee= marketer_total.get("TotalFee"),
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
