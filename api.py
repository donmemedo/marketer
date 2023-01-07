from fastapi import FastAPI
from config import setting
from database import get_database
from models import SearchUser


app = FastAPI(version=setting.VERSION)


def cleaner(items: list):
    for item in items:
        if '_id' in item:
            del item['_id']

    return items


@app.get("/user")
def get_user():
    PAGE_SIZE = 5
    PAGE_NUMBER = 1

    db = get_database()
    customer_coll = db['customers']
    docs = customer_coll.find({}).skip(PAGE_NUMBER).limit(PAGE_SIZE)

    response = [doc for doc in docs]

    cleaner(response) 

    return {
        "page": PAGE_NUMBER,
        "page_size": PAGE_SIZE,
        "content": response
        }


@app.get("/sub_users")
def get_sub_users():
    PAGE_NUMBER = 5
    PAGE_SIZE = 6
    NAME = 'نسرین'

    db = get_database()

    customer_coll = db['customers']

    docs = customer_coll.find({'Referer': {'$regex': NAME }}).skip(PAGE_NUMBER).limit(PAGE_SIZE)

    response = [doc for doc in docs]

    print(response)

    cleaner(response)

    return {
        "page": PAGE_NUMBER,
        "page_size": PAGE_SIZE,
        "content": response
    }


@app.get('/search_user')
def search_marketer_user(user: SearchUser):

    print(user.dic()) 
    #db = get_database()

    #customer_coll = db['customers']

    #print(user.username)
    #docs = customer_coll.find({'Username': user.username})

    return 2
