from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pymongo import ASCENDING, MongoClient

from src.auth.authentication import get_current_user
from src.auth.authorization import authorize
from src.schemas.schemas import ResponseListOut, UserSearchIn
from src.tools.database import get_database
from src.tools.utils import get_marketer_name

user_router = APIRouter(prefix="/user", tags=["User"])


@user_router.get("/search", response_model=None)
@authorize(["Marketer.All"])
async def get_user_profile(
        user: dict = Depends(get_current_user),
        args: UserSearchIn = Depends(UserSearchIn),
        brokerage: MongoClient = Depends(get_database),
):
    # check whether marketer exists or not and return his name
    query_result = brokerage.marketers.find_one({"IdpId": user.get("sub")})

    if query_result is None:
        return HTTPException(status_code=401, detail="Unauthorized User")

    marketer_fullname = get_marketer_name(query_result)

    pipeline = [
        {"$match": {"$and": [{"Referer": marketer_fullname}]}},
        {
            "$project": {
                "Name": {"$concat": ["$FirstName", " ", "$LastName"]},
                "RegisterDate": 1,
                "Mobile": 1,
                "BankAccountNumber": 1,
                "Username": 1,
                "TradeCode": "$PAMCode",
                "FirstName": 1,
                "LastName": 1,
                "_id": 0,
                "FirmTitle": 1,
                "Telephone": 1,
                "FirmRegisterDate": 1,
                "Email": 1,
                "ActivityField": 1,
            }
        },
        {
            "$match": {
                "$or": [
                    {"Name": {"$regex": args.name}},
                    {"FirmTitle": {"$regex": args.name}},
                ]
            }
        },
        {"$sort": {"RegisterDate": ASCENDING}},
        {
            "$facet": {
                "metadata": [{"$count": "total"}],
                "items": [
                    {"$skip": (args.page_index - 1) * args.page_size},
                    {"$limit": args.page_size},
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

    results = brokerage.customers.aggregate(pipeline=pipeline)

    result_dict = next(results, None)

    if result_dict:
        result = {
            "pagedData": result_dict.get("items", []),
            "errorCode": None,
            "errorMessage": None,
            "totalCount": result_dict.get("total", 0),
        }

        return ResponseListOut(timeGenerated=datetime.now(), result=result, error="")
    else:
        result = {
            "pagedData": [],
            "errorCode": None,
            "errorMessage": None,
            "totalCount": 0,
        }

        return ResponseListOut(timeGenerated=datetime.now(), result=result, error="")
