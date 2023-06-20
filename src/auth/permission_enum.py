from enum import Enum


class Service(Enum):
    Marketer = "مارکتر"


class Modules(Enum):
    All = "همه"


class Actions(Enum):
    Read = "خواندن"
    Write = "نوشتن"
    Delete = "حذف"
    Create = "ایجاد کردن"
    Update = "به روز رسانی"
    All = "همه"
