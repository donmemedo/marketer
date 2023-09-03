from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from khayyam import JalaliDatetime as jd
from pymongo import MongoClient
from src.tools.messages import errors
from src.tools.config import setting
from src.auth.authentication import get_current_user
from src.auth.authorization import authorize
from src.schemas.schemas import CostIn, FactorIn, ResponseOut, MarketerTotalIn, ErrorOut
from src.tools.database import get_database
from src.tools.utils import peek, to_gregorian_, get_marketer_name
from src.tools.queries import *

plan_router = APIRouter(prefix="/marketer", tags=["Marketer"])


@plan_router.get("/profile")
@authorize(["Marketer.All"])
async def get_marketer_profile(
        user: dict = Depends(get_current_user),
        brokerage: MongoClient = Depends(get_database),
):
    # result = brokerage.marketers.find_one({"IdpId": user.get("sub")}, {"_id": 0})
    marketers_col = brokerage[setting.MARKETERS_COLLECTION]
    result = marketers_col.find_one({"Id": user.get("sub")}, {"_id": 0})

    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    if result:
        return ResponseOut(timeGenerated=datetime.now(), result=result, error="")
    else:
        return ResponseOut(timeGenerated=datetime.now(), result={}, error="")


@plan_router.get("/cost")
@authorize(["Marketer.All"])
async def cal_marketer_cost(
        user: dict = Depends(get_current_user),
        args: CostIn = Depends(CostIn),
        brokerage: MongoClient = Depends(get_database)
):
    # check if marketer exists and return his name
    marketer_dict = brokerage.marketers.find_one({"IdpId": user.get("sub")}, {"_id": 0})

    if marketer_dict is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized user")

    # query = {"Referer": {"$regex": marketer_dict.get("FirstName")}}
    marketer_fullname = get_marketer_name(marketer_dict)
    query = {"Referer": marketer_fullname}

    fields = {"PAMCode": 1}

    customers_records = brokerage.customers.find(query, fields)
    trade_codes = [c.get("PAMCode") for c in customers_records]

    from_gregorian_date = args.from_date
    to_gregorian_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


    buy_pipeline = [
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}},
                    {"TradeDate": {"$gte": from_gregorian_date}},
                    {"TradeDate": {"$lte": to_gregorian_date}},
                    {"TradeType": 1},
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
                    "$add": ["$TotalCommission", {"$multiply": ["$Price", "$Volume"]}]
                },
            }
        },
        {
            "$group": {
                "_id": "$id",
                "TotalFee": {"$sum": "$TradeItemBroker"},
                "TotalBuy": {"$sum": "$Buy"},
            }
        },
        {"$project": {"_id": 0, "TotalBuy": 1, "TotalFee": 1}},
    ]

    sell_pipeline = [
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}},
                    {"TradeDate": {"$gte": from_gregorian_date}},
                    {"TradeDate": {"$lte": to_gregorian_date}},
                    {"TradeType": 2},
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
                        "$TotalCommission",
                    ]
                },
            }
        },
        {
            "$group": {
                "_id": "$id",
                "TotalFee": {"$sum": "$TradeItemBroker"},
                "TotalSell": {"$sum": "$Sell"},
            }
        },
        {"$project": {"_id": 0, "TotalSell": 1, "TotalFee": 1}},
    ]

    buy_agg_result = peek(brokerage.trades.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(brokerage.trades.aggregate(pipeline=sell_pipeline))

    marketer_total = {"TotalPureVolume": 0, "TotalFee": 0}

    buy_dict = {"vol": 0, "fee": 0}

    sell_dict = {"vol": 0, "fee": 0}

    if buy_agg_result:
        buy_dict["vol"] = buy_agg_result.get("TotalBuy")
        buy_dict["fee"] = buy_agg_result.get("TotalFee")

    if sell_agg_result:
        sell_dict["vol"] = sell_agg_result.get("TotalSell")
        sell_dict["fee"] = sell_agg_result.get("TotalFee")

    marketer_total["TotalPureVolume"] = buy_dict.get("vol") + sell_dict.get("vol")
    marketer_total["TotalFee"] = buy_dict.get("fee") + sell_dict.get("fee")

    # find marketer's plan
    marketer_plans = {
        "payeh": {"start": 0, "end": 30000000000, "marketer_share": 0.05},
        "morvarid": {"start": 30000000000, "end": 50000000000, "marketer_share": 0.1},
        "firouzeh": {"start": 50000000000, "end": 100000000000, "marketer_share": 0.15},
        "aghigh": {"start": 100000000000, "end": 150000000000, "marketer_share": 0.2},
        "yaghout": {"start": 150000000000, "end": 200000000000, "marketer_share": 0.25},
        "zomorod": {"start": 200000000000, "end": 300000000000, "marketer_share": 0.3},
        "tala": {"start": 300000000000, "end": 400000000000, "marketer_share": 0.35},
        "almas": {"start": 400000000000, "marketer_share": 0.4},
    }

    pure_fee = marketer_total.get("TotalFee") * 0.65
    marketer_fee = 0
    tpv = marketer_total.get("TotalPureVolume")

    if marketer_plans["payeh"]["start"] <= tpv < marketer_plans["payeh"]["end"]:
        marketer_fee = pure_fee * marketer_plans["payeh"]["marketer_share"]
        plan = "Payeh"
        next_plan = marketer_plans["payeh"]["end"] - pure_fee
    elif marketer_plans["morvarid"]["start"] <= tpv < marketer_plans["morvarid"]["end"]:
        marketer_fee = pure_fee * marketer_plans["morvarid"]["marketer_share"]
        plan = "Morvarid"
        next_plan = marketer_plans["morvarid"]["end"] - pure_fee
    elif marketer_plans["firouzeh"]["start"] <= tpv < marketer_plans["firouzeh"]["end"]:
        marketer_fee = pure_fee * marketer_plans["firouzeh"]["marketer_share"]
        plan = "Firouzeh"
        next_plan = marketer_plans["firouzeh"]["end"] - pure_fee
    elif marketer_plans["aghigh"]["start"] <= tpv < marketer_plans["aghigh"]["end"]:
        marketer_fee = pure_fee * marketer_plans["aghigh"]["marketer_share"]
        plan = "Aghigh"
        next_plan = marketer_plans["aghigh"]["end"] - pure_fee
    elif marketer_plans["yaghout"]["start"] <= tpv < marketer_plans["yaghout"]["end"]:
        marketer_fee = pure_fee * marketer_plans["yaghout"]["marketer_share"]
        plan = "Yaghout"
        next_plan = marketer_plans["yaghout"]["end"] - pure_fee
    elif marketer_plans["zomorod"]["start"] <= tpv < marketer_plans["zomorod"]["end"]:
        marketer_fee = pure_fee * marketer_plans["zomorod"]["marketer_share"]
        plan = "Zomorod"
        next_plan = marketer_plans["zomorod"]["end"] - pure_fee
    elif marketer_plans["tala"]["start"] <= tpv < marketer_plans["tala"]["end"]:
        marketer_fee = pure_fee * marketer_plans["tala"]["marketer_share"]
        plan = "Tala"
        next_plan = marketer_plans["tala"]["end"] - pure_fee
    elif marketer_plans["almas"]["start"] <= tpv:
        marketer_fee = pure_fee * marketer_plans["almas"]["marketer_share"]
        plan = "Almas"
        next_plan = 0

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
        tax = marketer_fee * args.tax
        final_fee -= tax

    if args.collateral != 0:
        collateral = marketer_fee * args.collateral
        final_fee -= collateral
    if args.tax == 0 and args.collateral == 0:
        collateral = marketer_fee * 0.05
        tax = marketer_fee * 0.1
        final_fee -= final_fee * 0.15
    two_months_ago_coll = 0

    result = {
        "TotalFee": marketer_total.get("TotalFee"),
        "PureFee": pure_fee,
        "MarketerFee": marketer_fee,
        "Plan": plan,
        "Next Plan": next_plan,
        "Tax": tax,
        "Collateral": collateral,
        "FinalFee": final_fee,
        "CollateralOfTwoMonthAgo": two_months_ago_coll,
        "Payment": final_fee + float(two_months_ago_coll),
    }

    return ResponseOut(timeGenerated=datetime.now(), result=result, error="")


@plan_router.get("/factor-print/")
@authorize(["Marketer.All"])
async def factor_print(
        user: dict = Depends(get_current_user),
        args: FactorIn = Depends(FactorIn),
        brokerage: MongoClient = Depends(get_database),
):
    factors_coll = brokerage["factors"]
    marketer = factors_coll.find_one({"IdpID": user.get("sub")})
    dd = args.year + f"{int(args.month):02}"
    cc = args.year + f"{int(args.month) - 2:02}"
    if args.month == "1" or args.month == "01":
        cc = str(int(args.year) - 1) + "11"
    if args.month == "2" or args.month == "02":
        cc = str(int(args.year) - 1) + "12"
    two_months_ago_coll = marketer[cc + "Collateral"]

    result = {
        "TotalFee": marketer[dd + "TotalFee"],
        "TotalPureVolume": marketer[dd + "TotalPureVolume"],
        "PureFee": marketer[dd + "PureFee"],
        "MarketerFee": marketer[dd + "MarketerFee"],
        "TotalFeeOfFollowers": marketer[dd + "TotalFeeOfFollowers"],
        "Collateral": marketer[dd + "CollateralOfThisMonth"],
        "Deductions": marketer[dd + "SumOfDeductions"],
        "Payment": marketer[dd + "Payment"],
    }

    return ResponseOut(timeGenerated=datetime.now(), result=result, error="")


@plan_router.get("/marketer-total", response_model=None)
@authorize(["Marketer.All"])
async def get_marketer_total_trades(
        user: dict = Depends(get_current_user),
        args: MarketerTotalIn = Depends(MarketerTotalIn),
        brokerage: MongoClient = Depends(get_database),
) -> JSONResponse:
    query_result = brokerage.marketers.find_one({"IdpId": user.get("sub")})
    if query_result is None:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("MARKETER_NOT_DEFINED"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )
    marketer_fullname = get_marketer_name(query_result)
    query = {"Referer": {"$regex": marketer_fullname}}
    trade_codes = brokerage.customers.distinct("PAMCode", query)
    from_gregorian_date = args.from_date
    to_gregorian_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")


    pipeline = [
        filter_users_stage(trade_codes, from_gregorian_date, to_gregorian_date),
        project_commission_stage(),
        group_by_total_stage("id"),
        project_pure_stage()
    ]

    result = next(brokerage.trades.aggregate(pipeline=pipeline), [])
    followers = dict(enumerate(brokerage.mrelations.find({"LeaderMarketerID": user.get("sub")},{"_id":0})))
    FTF = 0
    for i in followers:
        query = {"Referer": followers[i]['FollowerMarketerName']}

        trade_codes = brokerage.customers.distinct("PAMCode", query)
        from_gregorian_date = args.from_date
        to_gregorian_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        pipeline = [
            filter_users_stage(trade_codes, from_gregorian_date, to_gregorian_date),
            project_commission_stage(),
            group_by_total_stage("id"),
            project_pure_stage()
        ]
        fresult = next(brokerage.trades.aggregate(pipeline=pipeline), [])
        FTF = FTF + fresult['TotalFee']*followers[i]['CommissionCoefficient']
    result["TotalFeeOfFollowers"] = FTF

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            ResponseOut(
                timeGenerated=datetime.now(),
                result=result,
                error=""
            )
        )
    )


