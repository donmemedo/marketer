from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, IntEnum
from typing import Any, Dict, List

from fastapi import Query
from khayyam import JalaliDatetime

current_date = JalaliDatetime.today().replace(day=1).strftime("%Y-%m-%d")


@dataclass
class UserSearchIn:
    name: str = Query("", alias="Name")
    page_index: int = Query(1, alias="PageNumber")
    page_size: int = Query(5, alias="PageSize")


@dataclass
class UserTotalIn:
    trade_code: str = Query(alias="TradeCode")
    from_date: str = Query(default=current_date, alias="StartDate")
    to_date: str = Query(default=current_date, alias="EndDate")


@dataclass
class MarketerTotalIn:
    from_date: str = Query(default=current_date, alias="StartDate")
    to_date: str = Query(default=current_date, alias="EndDate")


@dataclass
class UserTotalOut:
    TotalPureVolume: float
    TotalFee: float


@dataclass
class ResponseOut:
    timeGenerated: datetime
    result: List[UserTotalOut] = List[Any]
    error: str = Query("nothing")


@dataclass
class ErrorOut:
    timeGenerated: datetime
    result: Dict
    error: Dict


@dataclass
class ResponseListOut:
    timeGenerated: datetime
    result: Dict
    error: str = Query("nothing")


@dataclass
class UserTotalOutList:
    result: dict[UserTotalOut]


@dataclass
class CostIn:
    insurance: int = Query(0, alias="Insurance")
    tax: int = Query(0, alias="Tax")
    salary: int = Query(0, alias="Salary")
    collateral: int = Query(0, alias="Collateral")
    from_date: str = Query(current_date, alias="StartDate")
    to_date: str = Query(current_date, alias="EndDate")


@dataclass
class MarketerInvitationIn:
    id: int
    invitation_link: str


@dataclass
class Pages:
    size: int = Query(10, alias="PageSize")
    page: int = Query(1, alias="PageNumber")


class UserTypeEnum(str, Enum):
    active = "active"
    inactive = "inactive"


class SortField(str, Enum):
    REGISTRATION_DATE = "RegisterDate"
    TotalPureVolume = "TotalPureVolume"


class SortOrder(IntEnum):
    ASCENDING = 1
    DESCENDING = -1


@dataclass
class UsersListIn(Pages):
    sort_by: SortField = Query(SortField.REGISTRATION_DATE, alias="SortBy")
    sort_order: SortOrder = Query(SortOrder.ASCENDING, alias="SortOrder")
    user_type: UserTypeEnum = Query(UserTypeEnum.active, alias="UserType")
    from_date: str = Query(date.today().isoformat(), alias="StartDate")
    to_date: str = Query(date.today().isoformat(), alias="EndDate")


@dataclass
class FactorIn:
    insurance: int = Query(0)
    tax: int = Query(0)
    salary: int = Query(0)
    collateral: int = Query(0)
    month: str = Query(JalaliDatetime.today().month)
    year: str = Query(JalaliDatetime.today().year)
