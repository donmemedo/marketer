from fastapi import FastAPI, HTTPException
from config import setting
from database import get_database
from schemas import SearchUser
from datetime import timedelta, date
from tools import cleaner
import uvicorn


app = FastAPI(version=setting.VERSION, title=setting.SWAGGER_TITLE)


@app.get("/get_all_users_trades/{marketer_name}", tags=["users"])
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


@app.get("/get_user_total_trades/{trade_code}", tags=["trades"])
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


@app.get("/search_user/{marketer_name}", tags=["users"])
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
    total_records = customer_coll.count_documents(query)
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


@app.get("/user_profile/", tags=["users"])
async def get_user_profile(first_name: str='', last_name: str='', marketer_name: str='', page_size: int=1, page_index: int=0):
    db = get_database()

    customer_coll = db["customers"]

    query = {"$and": [
        {"Referer": {"$regex": marketer_name}},
        {"FirstName": {"$regex": first_name}},
        {"LastName": {"$regex": last_name }}
        ]
    }

    fields = {
        "Username": 1,
        "PAMCode": 1
    }

    total_records = customer_coll.count_documents(query)

    docs = customer_coll.find(query, fields).skip(page_index).limit(page_size)
    response = [d for d in docs]

    cleaner(response)

    return { "TotalRecords": total_records, "Response": response}


@app.get("/get_user_fee", tags=["users"])
async def get_user_fee(marketer_name, trade_code):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": marketer_name}},
        {"PAMCode": trade_code}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c for c in customers_records]

    if not trade_codes:
        raise HTTPException(status_code=404, detail="Customer Not Found")
    else:
        pipeline = [
            {"$match": {"TradeCode": trade_code}},
            {
                "$group": {
                    "_id": "$id", 
                    "TotalVolume": {
                        "$sum": "$TradeItemBroker"
                        }
                    }
                },
            ]
         
        agg_result = trades_coll.aggregate(pipeline=pipeline)

        return (cleaner([a for a in agg_result]))


@app.get("/users_total_fee/{marketer_name}", tags=["users"])
async def get_users_total_fee(marketer_name):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": marketer_name}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    pipeline = [
        {"$match": {"TradeCode": {"$in": trade_codes}}},
        {
            "$group": {
                "_id": "$id", 
                "TotalVolume": {
                    "$sum": "$TradeItemBroker"
                    }
                }
        }
    ]

    agg_result = trades_coll.aggregate(pipeline=pipeline)

    return ([a for a in agg_result])


@app.get("/marketer/", tags=["marketers"])
async def get_marketer_profile(name: str=''):
    db = get_database()

    marketers_coll = db["marketers"]
    query = {"FirstName": {"$regex": name}}

    query_result = marketers_coll.find(query)
    return cleaner([r for r in query_result])


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)

    # TODO: use motor to async all database connections
    # TODO: add response model to all APIs
