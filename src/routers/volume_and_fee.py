from datetime import datetime, timedelta

import fastapi.responses
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from khayyam import JalaliDatetime
from pymongo import MongoClient

from src.auth.authentication import get_current_user
from src.auth.authorization import authorize
from src.schemas.schemas import (MarketerTotalIn, ResponseListOut, ResponseOut,
                                 UsersListIn, UserTotalIn)
from src.tools.database import get_database
from src.tools.queries import *
from src.tools.utils import get_marketer_name, to_gregorian_

volume_and_fee_router = APIRouter(prefix="/volume-and-fee", tags=["Volume and Fee"])


@volume_and_fee_router.get("/user-total", response_model=None)
@authorize(["Marketer.All"])
async def get_user_total_trades(
        user: dict = Depends(get_current_user),
        args: UserTotalIn = Depends(UserTotalIn),
        brokerage: MongoClient = Depends(get_database),
):
    # check if marketer exists and return his name
    query_result = brokerage.marketers.find_one({"IdpId": user.get("sub")})

    if query_result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized User")

    # transform date from Jalali to Gregorian
    from_gregorian_date = to_gregorian_(args.from_date)
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(
        days=1
    )
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

    pipeline = [
        filter_users_stage([args.trade_code], from_gregorian_date, to_gregorian_date),
        project_commission_stage(),
        group_by_total_stage("$TradeCode"),
        project_pure_stage(),
        join_customers_stage(),
        unwind_user_stage(),
        project_fields_stage()
    ]

    result = next(brokerage.trades.aggregate(pipeline=pipeline), [])

    return ResponseOut(
        result=result,
        timeGenerated=JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
        error=""
    )


@volume_and_fee_router.get("/marketer-total", response_model=None)
@authorize(["Marketer.All"])
async def get_marketer_total_trades(
        user: dict = Depends(get_current_user),
        args: MarketerTotalIn = Depends(MarketerTotalIn),
        brokerage: MongoClient = Depends(get_database),
):
    # check if marketer exists and return his name
    query_result = brokerage.marketers.find_one({"IdpId": user.get("sub")})

    if query_result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized User")

    marketer_fullname = get_marketer_name(query_result)

    # Get all customers
    query = {"Referer": {"$regex": marketer_fullname}}

    trade_codes = brokerage.customers.distinct("PAMCode", query)

    # transform date from Jalali to Gregorian
    from_gregorian_date = to_gregorian_(args.from_date)
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(
        days=1
    )
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

    pipeline = [
        filter_users_stage(trade_codes, from_gregorian_date, to_gregorian_date),
        project_commission_stage(),
        group_by_total_stage("id"),
        project_pure_stage()
    ]

    result = next(brokerage.trades.aggregate(pipeline=pipeline), [])

    return ResponseOut(timeGenerated=datetime.now(), result=result, error="")


@volume_and_fee_router.get("/users-total", response_model=None)
@authorize(["Marketer.All"])
async def users_list_by_volume(
        user: dict = Depends(get_current_user),
        args: UsersListIn = Depends(UsersListIn),
        brokerage: MongoClient = Depends(get_database),
):
    # check if marketer exists and return his name
    try:
        JalaliDatetime.strptime(args.to_date, "%Y-%m-%d").todatetime()
    except:
        resp = {
            "result": [],
            "timeGenerated": JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "error": {
                "message": "تاریخ انتها را درست وارد کنید.",
                "code": "30010",
            },
        }
        return JSONResponse(status_code=412, content=resp)
    try:
        JalaliDatetime.strptime(args.from_date, "%Y-%m-%d").todatetime()
    except:
        resp = {
            "result": [],
            "timeGenerated": JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "error": {
                "message": "تاریخ ابتدا را درست وارد کنید.",
                "code": "30010",
            },
        }
        return JSONResponse(status_code=412, content=resp)
    query_result = brokerage.marketers.find_one({"IdpId": user.get("sub")})

    if not query_result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized User")

    marketer_fullname = get_marketer_name(query_result)

    from_gregorian_date = to_gregorian_(args.from_date)
    to_gregorian_date = to_gregorian_(args.to_date)
    to_gregorian_date = datetime.strptime(to_gregorian_date, "%Y-%m-%d") + timedelta(
        days=1
    )
    to_gregorian_date = to_gregorian_date.strftime("%Y-%m-%d")

    # from_gregorian_date = args.from_date
    # to_gregorian_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    query = {"Referer": {"$regex": marketer_fullname}}

    trade_codes = brokerage.customers.distinct("PAMCode", query)

    if args.user_type.value == "active":
        pipeline = [
            filter_users_stage(trade_codes, from_gregorian_date, to_gregorian_date),
            project_commission_stage(),
            group_by_total_stage("$TradeCode"),
            project_pure_stage(),
            join_customers_stage(),
            unwind_user_stage(),
            project_fields_stage(),
            sort_stage(args.sort_by.value, args.sort_order.value),
            paginate_data(args.page, args.size),
            unwind_metadata_stage(),
            project_total_stage()
        ]

        active_dict = next(brokerage.trades.aggregate(pipeline=pipeline), {})

        result = {
            "pagedData": active_dict.get("items", []),
            "errorCode": None,
            "errorMessage": None,
            "totalCount": active_dict.get("total", 0),
        }

        return ResponseListOut(timeGenerated=datetime.now(), result=result, error="")

    elif args.user_type.value == "inactive":
        active_users_pipeline = [
            filter_users_stage(trade_codes, from_gregorian_date, to_gregorian_date),
            group_by_trade_code_stage(),
            project_by_trade_code_stage()
        ]

        active_users_res = brokerage.trades.aggregate(pipeline=active_users_pipeline)
        active_users_set = set(i.get("TradeCode") for i in active_users_res)

        # check whether it is empty or not
        inactive_users_set = set(trade_codes) - active_users_set

        inactive_users_pipeline = [
            match_inactive_users(list(inactive_users_set)),
            project_inactive_users(),
            sort_stage(args.sort_by.value, args.sort_order.value),
            paginate_data(args.page, args.size),
            unwind_metadata_stage(),
            project_total_stage()
        ]

        inactive_dict = next(
            brokerage.customers.aggregate(pipeline=inactive_users_pipeline), {}
        )

        result = {
            "pagedData": inactive_dict.get("items", []),
            "errorCode": None,
            "errorMessage": None,
            "totalCount": inactive_dict.get("total", 0),
        }

        return ResponseListOut(timeGenerated=datetime.now(), result=result, error="")
