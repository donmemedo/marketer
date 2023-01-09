from fastapi import FastAPI
from config import setting
from database import get_database
from schemas import SearchUser
from datetime import timedelta, date
import uvicorn


app = FastAPI(version=setting.VERSION)


def cleaner(items: list):
    for item in items:
        if '_id' in item:
            del item['_id']

    return items


@app.get('/user_total_trades/{trade_code}')
def user_total_trades(trade_code: str):
    db = get_database()
    trades_coll = db['trades']

    # pipeline = [ {'$match': { 'TradeCode': trade_code}}, {'$group':  { '_id' : '$id', 'total':{'$sum':'$Volume'}}} ]
    # pipeline2 = [ {'$match': { 'TradeCode': trade_code}}, { '$project': { 'Price': 1, 'Volume': 1, 'total': { '$multiply': [ "$Price", "$Volume" ] } } }]
    pipeline = [ {'$match': { 'TradeCode': trade_code}}, { '$project': { 'Price': 1, 'Volume': 1, 'total': { '$multiply': [ "$Price", "$Volume" ] } } }, {'$group':  { '_id' : '$id', 'TotalVolume':{'$sum':'$total'}}} ]
    aggregate = trades_coll.aggregate(pipeline=pipeline)

    records = [r for r in aggregate]
    cleaner(records)
    return records


@app.get('/search_user/{marketer_name}')
def search_marketer_user(marketer_name: str, page_size: int = 1, page_index: int = 1):
    db = get_database()

    customer_coll = db['customers']

    query =  {
        'Referer': {
            '$regex': marketer_name 
            }
        }

    fields = {
        "Username": 1,
        "FirstName": 1,
        "LastName": 1,
        "PAMCode": 1,
        "BankAccountNumber": 1
        }


    docs = customer_coll.find(query, fields).skip(page_index).limit(page_size)
   

    users = [doc for doc in docs]

    cleaner(users)

    # TODO: currently we consider all users as customer, in future this must change
    for item in users:
        item.update( {'UserType': 'مشتری'} )


    trades_coll = db['trades']

    # get last month starting date
    today = date.today()
    last_month = today - timedelta(days=30)
    temporary = last_month.strftime('%Y-%m-%d')


    # TODO: add total records in the response

    # get user trade status
    for user in users:
        trades_response = trades_coll.find(
            {
                'TradeDate': { '$gt':  temporary },
                'TradeCode': user.get('PAMCode')
            }
        ).limit(1)

        # unfold the results 
        results = [d for d in trades_response]

        # specify whether the user is active or not
        if not results:
            user['UserStatus'] = "NotActive"
        else:
            user['UserStatus'] = "Active"
        
    return {
        "Results": users,
        "TotalRecords": None
    }

if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)
