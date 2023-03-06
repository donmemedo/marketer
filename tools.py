"""_summary_

Returns:
    _type_: _description_
"""
from datetime import date
from khayyam import JalaliDatetime


def remove_id(items: list):
    """_summary_

    Args:
        items (list): _description_

    Returns:
        _type_: _description_
    """
    for item in items:
        if "_id" in item:
            del item["_id"]

    return items


def to_gregorian(date_: date):
    """_summary_

    Args:
        date_ (date): _description_

    Returns:
        _type_: _description_
    """
    jalali_date = JalaliDatetime(
        year=date_.year,
        month=date_.month,
        day=date_.day
    )

    gregorian_date = jalali_date.todate().strftime("%Y-%m-%d")
    return gregorian_date


def to_gregorian_(date_string: str):
    """_summary_

    Args:
        date_string (str): _description_

    Returns:
        _type_: _description_
    """
    year, month, day = date_string.split('-')

    return JalaliDatetime(year, month, day).todate().strftime("%Y-%m-%d")


def peek(iterable):
    """_summary_

    Args:
        iterable (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return first
