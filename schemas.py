from fastapi import Query
from dataclasses import dataclass
from datetime import date
from khayyam import *
from pydantic import BaseModel
from typing import Optional


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


class UserOut(BaseModel):
    FirstName: str
    LastName: str
    PAMCode: str
    Username: Optional[str]
    Mobile: str
    RegisterDate: str
    BankAccountNumber: str


@dataclass
class UsersTotalVolumeIn:
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
    to_date: date = Query(current_date)


@dataclass
class SearchUserIn:
    page_index: int = Query(0)
    page_size: int = Query(5)


@dataclass
class UserFee:
    trade_code: str
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)


@dataclass
class UserTotalFee:
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)


@dataclass
class UsersTotalPureIn:
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)


@dataclass
class PureOut:
    Result: list
    Error: str
    TimeGenerated: str


@dataclass
class PureLastNDaysIn:
    last_n_days: int


@dataclass
class CostIn(BaseModel):
    salary: int
    insurance: int
    collateral: int
    tax: int


@dataclass
class MarketerInvitationIn():
    id: int
    invitation_link: str


class MarketerInvitationOut(BaseModel):
    Id: int
    FirstName: str
    LastName: str
    IsOrganization: str
    RefererType: str
    CreatedBy: str
    CreateDate: str
    ModifiedBy: str
    ModifiedDate: str
    InvitationLink: Optional[str] = ...