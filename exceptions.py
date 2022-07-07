
class _ParentException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class ValidateError(_ParentException):
    def __init__(self, text, *args):
        super().__init__(text, *args)
