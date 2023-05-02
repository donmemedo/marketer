from dataclasses import dataclass
from datetime import date
from typing import Optional
from fastapi import Query
from khayyam import JalaliDatetime
from pydantic import BaseModel
from enum import Enum, IntEnum


current_date = JalaliDatetime.today().replace(day=1).strftime("%Y-%m-%d")


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
    FirstName: Optional[str]
    LastName: Optional[str]
    PAMCode: str
    Username: Optional[str]
    Mobile: Optional[str]
    RegisterDate: Optional[str]
    BankAccountNumber: Optional[str]


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
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)


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
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)


@dataclass
class PureOut:
    Result: list
    Error: str
    TimeGenerated: str


@dataclass
class PureLastNDaysIn:
    last_n_days: int


@dataclass
class CostIn:
    insurance: int = Query(0)
    tax: int = Query(0)
    salary: int = Query(0)
    collateral: int = Query(0)
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)

@dataclass
class SubCostIn:
    first_name: str = Query("")
    last_name: str = Query("")
    phone: str = Query("")
    mobile: str = Query("")
    user_id: str = Query("")
    username: str = Query("")
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)


@dataclass
class MarketerInvitationIn():
    id: int
    invitation_link: str


@dataclass
class MarketerIdpIdIn():
    id: int
    idpid: str


class MarketerInvitationOut(BaseModel):
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
    first_name: str = Query("")
    last_name: str = Query("")
    register_date: str = Query("")
    phone: str = Query("")
    mobile: str = Query("")
    user_id: str = Query("")
    username: str = Query("")
    page_size: int = Query(5)
    page_index: int = Query(0)


class SubUserOut(BaseModel):
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
    size: int = Query(10)
    page: int = Query(1)


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
    sort_by: SortField = Query(SortField.REGISTRATION_DATE)
    sort_order: SortOrder = Query(SortOrder.ASCENDING)
    user_type: UserTypeEnum = Query(UserTypeEnum.active)
    from_date: str = Query(current_date)
    to_date: str = Query(current_date)