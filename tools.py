from khayyam import JalaliDatetime
from datetime import date


def remove_id(items: list):
    for item in items:
        if "_id" in item:
            del item["_id"]

    return items


def to_gregorian(date_: date):
    jalali_date = JalaliDatetime(
        year=date_.year,
        month=date_.month,
        day=date_.day
    )

    gregorian_date = jalali_date.todate().strftime("%Y-%m-%d")


    return gregorian_date
