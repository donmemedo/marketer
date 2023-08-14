class MarketerErrors:
    def __init__(self, message: str, code: int):
        self.message = message
        self.code = code


errors = {
    "MARKETER_NOT_DEFINED": MarketerErrors(
        code=1,
        message="حساب کاربری شما به عنوان مارکتر تعریف نشده است."
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
    )
}
