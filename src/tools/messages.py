class MarketerErrors:
    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code


errors = {
    "MARKETER_NOT_DEFINED1": MarketerErrors(
        code=11,
        message="حساب کاربری 1 به عنوان مارکتر تعریف نشده است."
    ),
    "MARKETER_NOT_DEFINED2": MarketerErrors(
        code=12,
        message="حساب کاربری 2 به عنوان مارکتر تعریف نشده است."
    ),
    "MARKETER_NOT_DEFINED3": MarketerErrors(
        code=13,
        message="حساب کاربری 3 به عنوان مارکتر تعریف نشده است."
    ),
    "MARKETER_NOT_DEFINED4": MarketerErrors(
        code=14,
        message="حساب کاربری 4 به عنوان مارکتر تعریف نشده است."
    ),
    "MARKETER_NOT_DEFINED5": MarketerErrors(
        code=15,
        message="حساب کاربری 5 به عنوان مارکتر تعریف نشده است."
    ),
    "MARKETER_NOT_DEFINED6": MarketerErrors(
        code=16,
        message="حساب کاربری 6 به عنوان مارکتر تعریف نشده است."
    ),
    "TOKEN_IS_INVALID": MarketerErrors(
        code=2,
        message="توکن نامعتبر است."
    ),
    "TOKEN_EXPIRED": MarketerErrors(
        code=3,
        message="توکن منقضی شده است."
    ),
    "INVALID_AUTHENTICATION_SCHEME": MarketerErrors(
        code=4,
        message="شمای احراز هویت نامعتبر است."
    ),
    "CANNOT_FETCH_PUBLIC_KEY": MarketerErrors(
        code=5,
        message="خطای عدم دسترسی به کلید عمومی سرویس احراز هویت"
    ),
    "MARKETER_FACTORS_NOT_FOUND": MarketerErrors(
        code=6,
        message="فاکتوری برای شما در دیتابیس وجود ندارد."
    )
}
