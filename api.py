from fastapi import FastAPI, HTTPException, Depends
from datetime import timedelta, date
import uvicorn
from schemas import *
from tools import remove_id, to_gregorian
from database import get_database
from config import setting


app = FastAPI(version=setting.VERSION, title=setting.SWAGGER_TITLE)


@app.get("/users_trades/", tags=["users"])
async def get_users_trades(args: MarketerUsersIn = Depends(MarketerUsersIn)):

    db = get_database()

    # set collections
    customer_coll = db["customers"]
    trades_coll = db["trades"]

    # transform date from Gregorian to Jalali calendar
    gregorian_date = to_gregorian(args.from_date)

    query = {"Referer": {"$regex": args.marketer_name}}

    fields = {"PAMCode": 1}

    records = customer_coll.find(query, fields).skip(args.page_index).limit(args.page_size)

    trade_codes = []

    for record in records:
        trade_codes.append(record["PAMCode"])

    response_list = []

    for trade_code in trade_codes:
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"TradeCode": trade_code}, 
                        {"TradeDate": {"$gte": gregorian_date}}
                        ]
                    }
                },
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
        remove_id(records)

        if not records:
            response_list.append({"TradeCode": trade_code, "TotalVolume": 0})
        else:
            response_list.append(*records)

    return response_list


@app.get("/user_total_trades/", tags=["users"])
async def get_user_total_trades(args: UserTotalTradesIn = Depends(UserTotalTradesIn)):
    db = get_database()
    trades_coll = db["trades"]

    # transform date from Gregorian to Jalali calendar
    gregorian_date = to_gregorian(args.from_date)

    pipeline = [
        {
            "$match": {
                "$and": [
                    {"TradeCode": args.trade_code},
                    {"TradeDate": {"$gt": gregorian_date}}
                    ]
                }
            },
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

    remove_id(records)


    return records


@app.get("/search_user/", tags=["users"])
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


@app.get("/user_profile/", tags=["users"])
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


@app.get("/user_fee", tags=["users"])
async def get_user_fee(args: UserFee = Depends(UserFee)):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}},
        {"PAMCode": args.trade_code}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c for c in customers_records]

    if not trade_codes:
        raise HTTPException(status_code=404, detail="Customer Not Found")
    else:
        pipeline = [
            {"$match": {"TradeCode": args.trade_code}},
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

        return (remove_id([a for a in agg_result]))


@app.get("/users_total_fee/", tags=["users"])
async def get_users_total_fee(args: UserTotalFee = Depends(UserTotalFee)):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    gregorian_date = to_gregorian(args.from_date)

    pipeline = [
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gt": gregorian_date}}
                    ]
                }
            },
        {
            "$group": {
                "_id": "$id", 
                "TotalFee": {
                    "$sum": "$TradeItemBroker"
                    }
                }
        }
    ]

    agg_result = trades_coll.aggregate(pipeline=pipeline)

    return ([a for a in agg_result])


@app.get("/users_total_trades", tags=["users"])
def get_users_total_trades(args: UsersTotalTradesIn = Depends(UsersTotalTradesIn)):
    db = get_database()

    customers_coll = db["customers"]
    trades_coll = db["trades"]

    # Check if customer exist
    query = {"$and": [
        {"Referer": {"$regex": args.marketer_name}}
        ]
    }

    fields = {"PAMCode": 1}

    customers_records = customers_coll.find(query, fields)
    trade_codes = [c.get('PAMCode') for c in customers_records]

    gregorian_date = to_gregorian(args.from_date)

    pipeline = [ 
        {
            "$match": {
                "$and": [
                    {"TradeCode": {"$in": trade_codes}}, 
                    {"TradeDate": {"$gt": gregorian_date}}
                    ]
                }
            },
        {
            "$project": {
                "Price": 1,
                "Volume": 1,
                "total" : {"$multiply": ["$Price", "$Volume"]}
            }
        },
        {
            "$group": {
                "_id": "$id", 
                "TotalVolume": {
                    "$sum": "$total"
                    }
                }
        }
    ]

    agg_result = trades_coll.aggregate(pipeline=pipeline)

    return ([a for a in agg_result])


@app.get("/marketer/", tags=["marketers"])
async def get_marketer_profile(args: MarketerIn = Depends(MarketerIn)):
    db = get_database()

    marketers_coll = db["marketers"]
    query = {"FirstName": {"$regex": args.name}}

    query_result = marketers_coll.find(query)
    return remove_id([r for r in query_result])


# TODO: implement marketers' costs
@app.get("/marketer_costs/", tags=["marketers"])
async def cal_marketer_costs():
    pass


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=8000)

    # TODO: use motor to async all database connections
    # TODO: add response model to all APIs
