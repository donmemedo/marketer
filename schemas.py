from fastapi import Query
from dataclasses import dataclass
from datetime import date
from khayyam import *


current_date = JalaliDatetime.today().replace(day=1).strftime("%Y-%m-%d")
print(current_date)


@dataclass
class MarketerIn:
    name: str = Query(...)


@dataclass
class UserIn:
    first_name: str = Query("")
    last_name: str = Query("")
    marketer_name: str = Query("")
    page_size: int = Query(5)
    page_index: int = Query(0)


@dataclass
class UsersTotalVolumeIn:
    marketer_name: str
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)
    page_index: int = Query(0)
    page_size: int = Query(5)


@dataclass
class UserTotalVolumeIn:
    trade_code: str
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)


@dataclass
class SearchUserIn:
    marketer_name: str
    page_index: int = Query(0)
    page_size: int = Query(5)


@dataclass
class UserFee:
    marketer_name: str
    trade_code: str


@dataclass
class UserTotalFee:
    marketer_name: str
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)


@dataclass
class UsersTotalPureIn:
    marketer_name: str 
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)


@dataclass
class PureLastNDaysIn:
    marketer_name: str
    last_n_days: int
