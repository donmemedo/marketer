from fastapi import FastAPI
from config import setting
from database import get_database
from schemas import SearchUser
from datetime import timedelta, date
import uvicorn


app = FastAPI(version=setting.VERSION)


def cleaner(items: list):
    for item in items:
        if "_id" in item:
            del item["_id"]

    return items


@app.get("/get_all_users_trades/{marketer_name}")
async def get_all_users_trades(
    marketer_name: str, page_index: int = 1, page_size: int = 1
):
    db = get_database()

    # set collections
    customer_coll = db["customers"]
    trades_coll = db["trades"]

    query = {"Referer": {"$regex": marketer_name}}

    fields = {"PAMCode": 1}

    records = customer_coll.find(query, fields).skip(page_index).limit(page_size)

    trade_codes = []

    for record in records:
        trade_codes.append(record["PAMCode"])

    response_list = []

    for trade_code in trade_codes:
        pipeline = [
            {"$match": {"TradeCode": trade_code}},
            {
                "$project": {
                    "TradeCode": 1,
                    "Price": 1,
                    "Volume": 1,
                    "total": {"$multiply": ["$Price", "$Volume"]},
                }
            },
            {
                "$group": {
                    "_id": "$id",
                    "TradeCode": {"$first": "$TradeCode"},
                    "TotalVolume": {"$sum": "$total"},
                }
            },
        ]
        aggregate = trades_coll.aggregate(pipeline=pipeline)

        records = [r for r in aggregate]
        cleaner(records)

        if not records:
            response_list.append({"TradeCode": trade_code, "TotalVolume": 0})
        else:
            response_list.append(*records)

    return response_list


@app.get("/get_user_total_trades/{trade_code}")
async def get_user_total_trades(trade_code: str):
    db = get_database()
    trades_coll = db["trades"]

    pipeline = [
        {"$match": {"TradeCode": trade_code}},
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "total": {"$multiply": ["$Price", "$Volume"]},
            }
        },
        {"$group": {"_id": "$id", "TotalVolume": {"$sum": "$total"}}},
    ]
    aggregate = trades_coll.aggregate(pipeline=pipeline)

    records = [r for r in aggregate]
    cleaner(records)
    return records


@app.get("/search_user/{marketer_name}")
async def search_marketer_user(
    marketer_name: str, page_size: int = 1, page_index: int = 1
):
    db = get_database()

    customer_coll = db["customers"]

    query = {"Referer": {"$regex": marketer_name}}

    fields = {
        "Username": 1,
        "FirstName": 1,
        "LastName": 1,
        "PAMCode": 1,
        "BankAccountNumber": 1,
    }

    docs = customer_coll.find(query, fields).skip(page_index).limit(page_size)

    users = [doc for doc in docs]

    cleaner(users)

    # TODO: currently we consider all users as customer, in future this must change
    for item in users:
        item.update({"UserType": "مشتری"})

    trades_coll = db["trades"]

    # get last month starting date
    today = date.today()
    last_month = today - timedelta(days=30)
    temporary = last_month.strftime("%Y-%m-%d")

    # TODO: add total records in the response

    # get user trade status
    for user in users:
        trades_response = trades_coll.find(
            {"TradeDate": {"$gt": temporary}, "TradeCode": user.get("PAMCode")}
        ).limit(1)

        # unfold the results
        results = [d for d in trades_response]

        # specify whether the user is active or not
        if not results:
            user["UserStatus"] = "NotActive"
        else:
            user["UserStatus"] = "Active"

    return {"Results": users, "TotalRecords": None}


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
