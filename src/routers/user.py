from fastapi import APIRouter, Depends
from tools import to_gregorian, remove_id
from schemas import SearchUserIn, UserIn
from database import get_database
from datetime import date, timedelta


user_router = APIRouter(prefix='/user', tags=['user'])


@user_router.get("/list/")
async def search_marketer_user(args: SearchUserIn = Depends(SearchUserIn)):
    db = get_database()

    customer_coll = db["customers"]

    query = {"Referer": {"$regex": args.marketer_name}}

    fields = {
        "Username": 1,
        "FirstName": 1,
        "LastName": 1,
        "PAMCode": 1,
        "BankAccountNumber": 1,
    }

    docs = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)
    total_records = customer_coll.count_documents(query)
    users = [doc for doc in docs]

    remove_id(users)

    # TODO: currently we consider all users as customer, in future this must change
    for item in users:
        item.update({"UserType": "مشتری"})

    trades_coll = db["trades"]

    # get last month starting date
    today = date.today()
    last_month = today - timedelta(days=30)
    temporary = last_month.strftime("%Y-%m-%d")

    # get user trade status
    for user in users:
        trades_response = trades_coll.find(
            {"TradeDate": {"$gt": temporary}, "TradeCode": user.get("PAMCode")}
        ).limit(1)

        # unfold the results
        results = [trade for trade in trades_response]

        # specify whether the user is active or not
        if not results:
            user["UserStatus"] = "NotActive"
        else:
            user["UserStatus"] = "Active"

    return {"Results": users, "TotalRecords": total_records}


@user_router.get("/profile/")
async def get_user_profile(args: UserIn = Depends(UserIn)):
    db = get_database()

    customer_coll = db["customers"]

    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}},
        {"FirstName": {"$regex": args.first_name}},
        {"LastName": {"$regex": args.last_name }}
        ]
    }

    fields = {
        "Username": 1,
        "PAMCode": 1
    }

    total_records = customer_coll.count_documents(query)

    docs = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)
    response = [d for d in docs]

    remove_id(response)

    return { "TotalRecords": total_records, "Response": response}
