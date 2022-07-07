
from fields import _Field


class Form:
    form_name: str

    _should_match: tuple  # Tuple of fields that values of each should match each other

    def __get_fields(self) -> dict:
        return {a: getattr(self, a) for a in self.__dir__() if isinstance(getattr(self, a), _Field)}

    def show_name(self):
        if self.form_name:
            print(f"=========={self.form_name.upper()}==========")

    def show(self) -> dict:
        res = dict()
        self.show_name()
        for field_name, field in self.__get_fields().items():
            field.render()
            res[field_name] = field.value
        return res

    def add_field(self, attr_name: str, field: _Field):
        return self.__setattr__(attr_name, field)

    def is_valid(self) -> bool:
        """Checks form's validity if there are specific params defined"""
        if hasattr(self, '_should_match'):
            if not all(self._should_match[0].value == field.value for field in self._should_match):
                return False
        return True
