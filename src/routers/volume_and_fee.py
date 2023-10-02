from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from khayyam import JalaliDatetime
from pymongo import MongoClient

from src.auth.authentication import get_current_user
from src.auth.authorization import authorize
from src.schemas.schemas import (MarketerTotalIn, ResponseListOut, ResponseOut,
                                 UsersListIn, UserTotalIn, ErrorOut)
from src.tools.database import get_database
from src.tools.messages import errors
from src.tools.queries import *
from src.tools.utils import get_marketer_name, to_gregorian_
from src.tools.config import setting

volume_and_fee_router = APIRouter(prefix="/volume-and-fee", tags=["Volume and Fee"])


@volume_and_fee_router.get("/user-total", response_model=None)
@authorize(["Marketer.All"])
async def get_user_total_trades(
        user: dict = Depends(get_current_user),
        args: UserTotalIn = Depends(UserTotalIn),
        brokerage: MongoClient = Depends(get_database),
) -> JSONResponse:
    # check if marketer exists and return his name
    marketers_coll = brokerage[setting.MARKETERS_COLLECTION]
    query_result = marketers_coll.find_one({"MarketerID": user.get("sub")})

    if query_result is None:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("MARKETER_NOT_DEFINED4"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )

    from_gregorian_date = args.from_date
    to_gregorian_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

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

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            ResponseOut(
                result=result,
                timeGenerated=datetime.now(),
                error=""
            )
        )
    )


@volume_and_fee_router.get("/marketer-total", response_model=None)
@authorize(["Marketer.All"])
async def get_marketer_total_trades(
        user: dict = Depends(get_current_user),
        args: MarketerTotalIn = Depends(MarketerTotalIn),
        brokerage: MongoClient = Depends(get_database),
) -> JSONResponse:
    # check if marketer exists and return his name
    marketers_coll = brokerage[setting.MARKETERS_COLLECTION]
    query_result = marketers_coll.find_one({"MarketerID": user.get("sub")})

    if query_result is None:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("MARKETER_NOT_DEFINED5"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )

    marketer_fullname = query_result["TbsReagentName"]#get_marketer_name(query_result)

    # Get all customers
    # query = {"Referer": {"$regex": marketer_fullname}}
    query = {"Referer": marketer_fullname}


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


@volume_and_fee_router.get("/users-total", response_model=None)
@authorize(["Marketer.All"])
async def users_list_by_volume(
        user: dict = Depends(get_current_user),
        args: UsersListIn = Depends(UsersListIn),
        brokerage: MongoClient = Depends(get_database),
) -> JSONResponse:
    # check if marketer exists and return his name
    try:
        JalaliDatetime.strptime(args.to_date, "%Y-%m-%d").todatetime()
    except:
        resp = {
            "result": [],
            "timeGenerated": datetime.now(),
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
            "timeGenerated": datetime.now(),
            "error": {
                "message": "تاریخ ابتدا را درست وارد کنید.",
                "code": "30010",
            },
        }
        return JSONResponse(status_code=412, content=resp)
    marketers_coll = brokerage[setting.MARKETERS_COLLECTION]
    query_result = marketers_coll.find_one({"MarketerID": user.get("sub")})

    if query_result is None:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content=jsonable_encoder(
                ErrorOut(
                    error=errors.get("MARKETER_NOT_DEFINED6"),
                    timeGenerated=datetime.now(),
                    result={}
                )
            )
        )

    marketer_fullname = query_result["TbsReagentName"]#get_marketer_name(query_result)
    from_gregorian_date = args.from_date
    to_gregorian_date = (datetime.strptime(args.to_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    # query = {"Referer": {"$regex": marketer_fullname}}
    query = {"Referer": marketer_fullname}


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

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(
                ResponseListOut(
                    timeGenerated=datetime.now(),
                    result=result,
                    error=""
                )
            )
        )

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

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(
                ResponseListOut(
                    timeGenerated=datetime.now(),
                    result=result,
                    error=""
                )
            )
        )
