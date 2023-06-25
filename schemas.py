"""_summary_
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Any, List, Dict
from fastapi import Query
# from khayyam import *
from khayyam import JalaliDatetime
from pydantic import BaseModel, Field
from enum import Enum, IntEnum

current_date = JalaliDatetime.today().replace(day=1).strftime("%Y-%m-%d")
current_month = JalaliDatetime.today().month
current_year = JalaliDatetime.today().year
# print(current_date)


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
    FirstName: Optional[str]
    LastName: Optional[str]
    PAMCode: str
    Username: Optional[str]
    Mobile: Optional[str]
    RegisterDate: Optional[str]
    BankAccountNumber: Optional[str]


@dataclass
class UsersTotalVolumeIn:
    """_summary_
    """
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")
    page_index: int = Query(0)
    page_size: int = Query(5)


@dataclass
class UserTotalVolumeIn:
    """_summary_
    """
    trade_code: str = Query(alias="TradeCode")
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: str = Query(default=current_date, alias="StartDate")
    to_date: str = Query(default=current_date, alias="EndDate")


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
    timeGenerated: JalaliDatetime
    result: List[UserTotalOut] = List[Any]
    error: str = Query("nothing")

@dataclass
class ResponseListOut:
    timeGenerated: JalaliDatetime
    result: Dict
    error: str = Query("nothing")


@dataclass
class UserTotalOutList:
    result: dict[UserTotalOut]


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
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")


@dataclass
class UserTotalFee:
    """_summary_
    """
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")


@dataclass
class UsersTotalPureIn:
    """_summary_
    """
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")


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
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")


@dataclass
class FactorIn:
    """_summary_
    """
    insurance: int = Query(0)
    tax: int = Query(0)
    salary: int = Query(0)
    collateral: int = Query(0)
    month: str = Query(current_month)
    year: str = Query(current_year)

@dataclass
class SubCostIn:
    """_summary_
    """
    first_name: str = Query("")
    last_name: str = Query("")
    phone: str = Query("")
    mobile: str = Query("")
    user_id: str = Query("")
    username: str = Query("")
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")


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

@dataclass
class SubUserIn:
    """_summary_
    """
    first_name: str = Query("")
    last_name: str = Query("")
    # marketer_name: str = Query("")
    register_date: str = Query("")
    phone: str = Query("")
    mobile: str = Query("")
    user_id: str = Query("")
    username: str = Query("")
    page_size: int = Query(5)
    page_index: int = Query(0)


class SubUserOut(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    FirstName: Optional[str]
    LastName: Optional[str]
    Referer: Optional[str]
    Username: Optional[str]
    Address: Optional[str]
    BankAccountNumber: Optional[str]
    AddressCity: Optional[str]
    FatherName: Optional[str]
    Email: Optional[str]
    BirthDate: Optional[str]
    IDSerial: Optional[str]
    BirthCertificateCity: Optional[str]
    BankName: Optional[str]
    IsInCreditContractTrading: Optional[str]
    PostalCode: Optional[str]
    BrokerBranchId: Optional[str]
    BrokerBranch: Optional[str]
    IDNumber: Optional[str]
    RegisterDate: Optional[str]
    ID: Optional[str]
    BankBranchName: Optional[str]
    Mobile: Optional[str]
    BankId: Optional[str]
    ModifiedDate: Optional[str]
    DetailLedgerCode: Optional[str]
    Phone: Optional[str]
    BourseCode: Optional[str]
    PAMCode: Optional[str]
    NationalCode: Optional[str]
@dataclass
class MarketerIn:
    """_summary_
    """
    first_name: str = Query("")
    last_name: str = Query("")
    # marketer_name: str = Query("")
    register_date: str = Query("")
    phone: str = Query("")
    mobile: str = Query("")
    user_id: str = Query("")
    username: str = Query("")
    page_size: int = Query(5)
    page_index: int = Query(0)


class MarketerOut(BaseModel):
    """_summary_

    Args:
        BaseModel (_type_): _description_
    """
    FirstName: Optional[str]
    LastName: Optional[str]
    CreateDate: Optional[str]
    CustomerType: Optional[str]
    IsOrganization: Optional[str]
    CreatedBy: Optional[str]
    InvitationLink: Optional[str]
    RefererType: Optional[str]
    IsEmployee: Optional[str]
    ID: Optional[str]
    IsCustomer: Optional[str]
    IdpId: Optional[str]
    ModifiedBy: Optional[str]
    ModifiedDate: Optional[str]


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
    from_date: str = Query(current_date, alias="StartDate")
    to_date: str = Query(current_date, alias="EndDate")

"""
# MAKh

@dataclass
class UsersListIn(Pages):
    from_date: str = Query(default=current_date, alias="EndDate")
    to_date: str = Query(default=current_date, alias="EndDate")
#
"""

@dataclass
class UsersTotalPureIn:
    # HACK: because Pydantic do not support Jalali Date, I had to use the universal calendar.
    # to_date: str = Query("1401-12-01")
    to_date: str = Query(default=None, alias="EndDate")
    from_date: str = Query(default=current_date, alias="EndDate")
    asc_desc_TPV: Optional[bool] = False
    asc_desc_TF: Optional[bool] = False
    asc_desc_LMTPV: Optional[bool] = False
    asc_desc_LMTF: Optional[bool] = False
    asc_desc_FN: Optional[bool] = False
    asc_desc_LN: Optional[bool] = False
    asc_desc_UC: Optional[bool] = False
    sorted: bool = False
