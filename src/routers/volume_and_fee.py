from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from khayyam import JalaliDatetime
from pymongo import MongoClient

from src.auth.authentication import get_current_user
from src.auth.authorization import authorize
from src.schemas.schemas import (MarketerTotalIn, ResponseListOut, ResponseOut,
                                 UsersListIn, UserTotalIn)
from src.tools.database import get_database
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
        {
            "$match": {
                "$and": [
                    {"TradeCode": args.trade_code},
                    {"TradeDate": {"$gte": from_gregorian_date}},
                    {"TradeDate": {"$lte": to_gregorian_date}},
                ]
            }
        },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total": {"$multiply": ["$Price", "$Volume"]},
                "TotalCommission": 1,
                "PriorityAcceptance": 1,
                "TradeItemBroker": 1,
                "TradeCode": 1,
                "Commission": {
                    "$cond": {
                        "if": {"$eq": ["$TradeType", 1]},
                        "then": {
                            "$add": [
                                "$TotalCommission",
                                {"$multiply": ["$Price", "$Volume"]},
                            ]
                        },
                        "else": {
                            "$subtract": [
                                {"$multiply": ["$Price", "$Volume"]},
                                "$TotalCommission",
                            ]
                        },
                    }
                },
            }
        },
        {
            "$group": {
                "_id": "$TradeCode",
                "TotalFee": {"$sum": "$TradeItemBroker"},
                "TotalPureVolume": {"$sum": "$Commission"},
                "TotalPriorityAcceptance": {"$sum": "$PriorityAcceptance"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "TradeCode": "$_id",
                "TotalPureVolume": {
                    "$add": ["$TotalPriorityAcceptance", "$TotalPureVolume"]
                },
                "TotalFee": 1,
            }
        },
        {
            "$lookup": {
                "from": "customers",
                "localField": "TradeCode",
                "foreignField": "PAMCode",
                "as": "UserProfile",
            }
        },
        {"$unwind": "$UserProfile"},
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
                "FirmTitle": "$UserProfile.FirmTitle",
                "Telephone": "$UserProfile.Telephone",
                "FirmRegisterLocation": "$UserProfile.FirmRegisterLocation",
                "Email": "$UserProfile.Email",
                "ActivityField": "$UserProfile.ActivityField",
            }
        },
    ]

    result = next(brokerage.trades.aggregate(pipeline=pipeline), None)

    if result:
        return ResponseOut(
            result=result,
            timeGenerated=JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            error="",
        )
    else:
        return ResponseOut(
            timeGenerated=JalaliDatetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            result=[],
            error="",
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
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}},
                    {"TradeDate": {"$gte": from_gregorian_date}},
                    {"TradeDate": {"$lte": to_gregorian_date}},
                ]
            }
        },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "Total": {"$multiply": ["$Price", "$Volume"]},
                "PriorityAcceptance": 1,
                "TotalCommission": 1,
                "TradeItemBroker": 1,
                "TradeCode": 1,
                "Commission": {
                    "$cond": {
                        "if": {"$eq": ["$TradeType", 1]},
                        "then": {
                            "$add": [
                                "$TotalCommission",
                                {"$multiply": ["$Price", "$Volume"]},
                            ]
                        },
                        "else": {
                            "$subtract": [
                                {"$multiply": ["$Price", "$Volume"]},
                                "$TotalCommission",
                            ]
                        },
                    }
                },
            }
        },
        {
            "$group": {
                "_id": "$id",
                "TotalFee": {"$sum": "$TradeItemBroker"},
                "TotalPureVolume": {"$sum": "$Commission"},
                "TotalPriorityAcceptance": {"$sum": "$PriorityAcceptance"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "TradeCode": "$_id",
                "TotalPureVolume": {
                    "$add": ["$TotalPriorityAcceptance", "$TotalPureVolume"]
                },
                "TotalFee": 1,
            }
        },
    ]

    result = next(brokerage.trades.aggregate(pipeline=pipeline), None)

    if result:
        return ResponseOut(timeGenerated=datetime.now(), result=result, error="")
    else:
        return ResponseOut(timeGenerated=datetime.now(), result=[], error="")


@volume_and_fee_router.get("/users-total", response_model=None)
@authorize(["Marketer.All"])
async def users_list_by_volume(
        user: dict = Depends(get_current_user),
        args: UsersListIn = Depends(UsersListIn),
        brokerage: MongoClient = Depends(get_database),
):
    # check if marketer exists and return his name
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

    query = {"Referer": {"$regex": marketer_fullname}}

    trade_codes = brokerage.customers.distinct("PAMCode", query)

    if args.user_type.value == "active":
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"TradeCode": {"$in": trade_codes}},
                        {"TradeDate": {"$gte": from_gregorian_date}},
                        {"TradeDate": {"$lte": to_gregorian_date}},
                    ]
                }
            },
            {
                "$project": {
                    "Price": 1,
                    "Volume": 1,
                    "Total": {"$multiply": ["$Price", "$Volume"]},
                    "PriorityAcceptance": 1,
                    "TotalCommission": 1,
                    "TradeItemBroker": 1,
                    "TradeCode": 1,
                    "Commission": {
                        "$cond": {
                            "if": {"$eq": ["$TradeType", 1]},
                            "then": {
                                "$add": [
                                    "$TotalCommission",
                                    {"$multiply": ["$Price", "$Volume"]},
                                ]
                            },
                            "else": {
                                "$subtract": [
                                    {"$multiply": ["$Price", "$Volume"]},
                                    "$TotalCommission",
                                ]
                            },
                        }
                    },
                }
            },
            {
                "$group": {
                    "_id": "$TradeCode",
                    "TotalFee": {"$sum": "$TradeItemBroker"},
                    "TotalPureVolume": {"$sum": "$Commission"},
                    "TotalPriorityAcceptance": {"$sum": "$PriorityAcceptance"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "TradeCode": "$_id",
                    "TotalPureVolume": {
                        "$add": ["$TotalPriorityAcceptance", "$TotalPureVolume"]
                    },
                    "TotalFee": 1,
                }
            },
            {
                "$lookup": {
                    "from": "customers",
                    "localField": "TradeCode",
                    "foreignField": "PAMCode",
                    "as": "UserProfile",
                }
            },
            {"$unwind": "$UserProfile"},
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
                    "FirmTitle": "$UserProfile.FirmTitle",
                    "Telephone": "$UserProfile.Telephone",
                    "FirmRegisterLocation": "$UserProfile.FirmRegisterLocation",
                    "Email": "$UserProfile.Email",
                    "ActivityField": "$UserProfile.ActivityField",
                }
            },
            {"$sort": {args.sort_by.value: args.sort_order.value}},
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "items": [
                        {"$skip": (args.page - 1) * args.size},
                        {"$limit": args.size},
                    ],
                }
            },
            {"$unwind": "$metadata"},
            {
                "$project": {
                    "total": "$metadata.total",
                    "items": 1,
                }
            },
        ]

        active_dict = next(brokerage.trades.aggregate(pipeline=pipeline), None)

        if active_dict is None:
            return {}

        result = {
            "pagedData": active_dict.get("items", []),
            "errorCode": None,
            "errorMessage": None,
            "totalCount": active_dict.get("total", 0),
        }

        return ResponseListOut(timeGenerated=datetime.now(), result=result, error="")

    elif args.user_type.value == "inactive":
        active_users_pipeline = [
            {
                "$match": {
                    "$and": [
                        {"TradeCode": {"$in": trade_codes}},
                        {"TradeDate": {"$gte": from_gregorian_date}},
                        {"TradeDate": {"$lte": to_gregorian_date}},
                    ]
                }
            },
            {"$group": {"_id": "$TradeCode"}},
            {"$project": {"_id": 0, "TradeCode": "$_id"}},
        ]

        active_users_res = brokerage.trades.aggregate(pipeline=active_users_pipeline)
        active_users_set = set(i.get("TradeCode") for i in active_users_res)

        # check wether it is empty or not
        inactive_uesrs_set = set(trade_codes) - active_users_set

        inactive_users_pipline = [
            {"$match": {"PAMCode": {"$in": list(inactive_uesrs_set)}}},
            {
                "$project": {
                    "_id": 0,
                    "TradeCode": 1,
                    "FirstName": 1,
                    "LastName": 1,
                    "Username": 1,
                    "Mobile": 1,
                    "RegisterDate": 1,
                    "BankAccountNumber": 1,
                    "FirmTitle": 1,
                    "Telephone": 1,
                    "FirmRegisterDate": 1,
                    "Email": 1,
                    "ActivityField": 1,
                }
            },
            {"$sort": {args.sort_by.value: args.sort_order.value}},
            {
                "$facet": {
                    "metadata": [{"$count": "total"}],
                    "items": [
                        {"$skip": (args.page - 1) * args.size},
                        {"$limit": args.size},
                    ],
                }
            },
            {"$unwind": "$metadata"},
            {
                "$project": {
                    "total": "$metadata.total",
                    "items": 1,
                }
            },
        ]

        inactive_dict = next(
            brokerage.customers.aggregate(pipeline=inactive_users_pipline), None
        )

        result = {
            "pagedData": inactive_dict.get("items", []),
            "errorCode": None,
            "errorMessage": None,
            "totalCount": inactive_dict.get("total", 0),
        }

        return ResponseListOut(timeGenerated=datetime.now(), result=result, error="")
    else:
        return ResponseListOut(timeGenerated=datetime.now(), result=[], error="")
