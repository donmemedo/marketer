from datetime import date
from khayyam import JalaliDatetime


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


def to_gregorian_(date_string: str):
    year, month, day = date_string.split('-')

    return JalaliDatetime(year, month, day).todate().strftime("%Y-%m-%d")


def peek(iterable):
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return first


def get_marketer_name(marketer_dict: dict):
    if marketer_dict.get("FirstName") == "":
        return marketer_dict.get("LastName")
    elif marketer_dict.get("LastName") == "":
        return marketer_dict.get("FirstName")
    else:
        return marketer_dict.get("FirstName") + " " + marketer_dict.get("LastName")
