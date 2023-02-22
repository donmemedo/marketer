"""_summary_
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional
from fastapi import Query
# from khayyam import *
from khayyam import JalaliDatetime
from pydantic import BaseModel


current_date = JalaliDatetime.today().replace(day=1).strftime("%Y-%m-%d")
print(current_date)


@dataclass
class MarketerIn:
    """_summary_
    """
    name: str = Query(...)


@dataclass
class UserIn:
    """_summary_
    """
    first_name: str = Query("")
    last_name: str = Query("")
    marketer_name: str = Query("")
    page_size: int = Query(5)
    page_index: int = Query(0)


class UserOut(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    FirstName: str
    LastName: str
    PAMCode: str
    Username: Optional[str]
    Mobile: Optional[str]
    RegisterDate: str
    BankAccountNumber: Optional[str]


@dataclass
class UsersTotalVolumeIn:
    """_summary_
    """
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)
    page_index: int = Query(0)
    page_size: int = Query(5)


@dataclass
class UserTotalVolumeIn:
    """_summary_
    """
    trade_code: str
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)


@dataclass
class SearchUserIn:
    """_summary_
    """
    page_index: int = Query(0)
    page_size: int = Query(5)


@dataclass
class UserFee:
    """_summary_
    """
    trade_code: str
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)


@dataclass
class UserTotalFee:
    """_summary_
    """
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: date = Query(current_date)
    to_date: date = Query(current_date)


@dataclass
class UsersTotalPureIn:
    """_summary_
    """
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)


@dataclass
class PureOut:
    """_summary_
    """
    Result: list
    Error: str
    TimeGenerated: str


@dataclass
class PureLastNDaysIn:
    """_summary_
    """
    last_n_days: int


@dataclass
class CostIn:
    """_summary_
    """
    insurance: int = Query(0)
    tax: int = Query(0)
    salary: int = Query(0)
    collateral: int = Query(0)
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)


@dataclass
class MarketerInvitationIn():
    """_summary_
    """
    id: int
    invitation_link: str


@dataclass
class MarketerIdpIdIn():
    """_summary_
    """
    id: int
    idpid: str


class MarketerInvitationOut(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    Id: Optional[int]
    FirstName: Optional[str]
    LastName: Optional[str]
    IsOrganization: Optional[str]
    RefererType: Optional[str]
    CreatedBy: Optional[str]
    CreateDate: Optional[str]
    ModifiedBy: Optional[str]
    ModifiedDate: Optional[str]
    InvitationLink: Optional[str] = ...
