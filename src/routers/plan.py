from datetime import timedelta, datetime
from khayyam import JalaliDatetime as jd
from fastapi import Depends, APIRouter, Request
from tools.database import get_database
from tools.tokens import JWTBearer, get_sub
from schemas.schemas import CostIn, ResponseOut, FactorIn
from tools.utils import to_gregorian_, peek


plan_router = APIRouter(prefix='/marketer', tags=['Marketer'])


@plan_router.get("/profile", dependencies=[Depends(JWTBearer())])
async def get_marketer_profile(request: Request):
    marketer_id = get_sub(request)
    brokerage = get_database()

    result = brokerage.marketers.find_one({"IdpId": marketer_id}, 
                                          {'_id': 0}
                                        )

    if result:
        return ResponseOut(timeGenerated=datetime.now(),
                           result=result,
                           error="")
    else:    
        return ResponseOut(timeGenerated=datetime.now(),
                           result={},
                           error="")


@plan_router.get("/cost", dependencies=[Depends(JWTBearer())])
async def cal_marketer_cost(request: Request, args: CostIn = Depends(CostIn)):
    marketer_id = get_sub(request)
    brokerage = get_database()

    # check if marketer exists and return his name
    marketer_dict = brokerage.marketers.find_one({"IdpId": marketer_id}, {"_id": 0})

    query = {"Referer": {"$regex": marketer_dict.get("FirstName")}}

    fields = {"PAMCode": 1}

    customers_records = brokerage.customers.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    # transform dates
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

    buy_agg_result = peek(brokerage.trades.aggregate(pipeline=buy_pipeline))
    sell_agg_result = peek(brokerage.trades.aggregate(pipeline=sell_pipeline))

    marketer_total = {
       "TotalPureVolume": 0,
       "TotalFee": 0
    }

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

    marketer_total["TotalPureVolume"] = buy_dict.get("vol") + sell_dict.get("vol")
    marketer_total["TotalFee"] = buy_dict.get("fee") + sell_dict.get("fee")

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
        "Payment": final_fee + float(two_months_ago_coll)
        }
    
    return ResponseOut(timeGenerated=datetime.now(),
                       result=result,
                       error=""
                    )


@plan_router.get("/factor-print/", dependencies=[Depends(JWTBearer())])
async def factor_print(request: Request, args: FactorIn = Depends(FactorIn)):
    marketer_id = get_sub(request)

    brokerage = get_database()
    marketers_coll = brokerage["marketers"]
    factors_coll = brokerage["factors"]
    marketer = factors_coll.find_one({"IdpID": marketer_id})
    dd=args.year+ f"{int(args.month):02}"
    cc=args.year+ f"{int(args.month)-2:02}"
    if args.month =="1" or args.month =="01":
        cc=str(int(args.year)-1)+ "11"
    two_months_ago_coll = marketer[cc+"Collateral"]
    from_date = f"{args.year}-{args.month}-01"
    from_gregorian_date = to_gregorian_(from_date)
    to_date = jd.strptime(from_date, "%Y-%m-%d")
    dorehh = f"{args.year} {to_date.monthname()}"
    to_date = to_date.replace(day=to_date.daysinmonth).strftime("%Y-%m-%d")
    to_gregorian_date = to_gregorian_(to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(days=1)
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

    result = {
        "TotalFee": marketer[dd+"TF"],
        "TotalPureVolume": marketer[dd+"TPV"],
        "PureFee": marketer[dd+"PureFee"],
        "MarketerFee": marketer[dd+"MarFee"],
        "Plan": marketer[dd+"Plan"],
        "Tax": marketer[dd+"Tax"],
        "Collateral": marketer[dd+"Collateral"],
        "FinalFee": marketer[dd+"FinalFee"],
        "CollateralOfTwoMonthAgo": two_months_ago_coll,
        "Payment": marketer[dd+"Payment"]
        }
    
    return ResponseOut(timeGenerated=datetime.now(),
                       result=result,
                       error=""
                    )
