import datetime
import decimal
import getpass
import re
import typing
import unittest.case
from abc import ABC, abstractmethod, abstractproperty

import exceptions
import utils

_DEFAULT_MAX_LENGTH = 256


class _Field(ABC):
    value_type: type
    label: str
    _value: typing.Any

    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @abstractmethod
    def render(self): ...


class _InputField(_Field):
    value_type = str

    def __init__(self, label: str, hint: str = None):
        super().__init__()
        self.label = label
        self.hint = hint

    def _convert_type(self, value):
        try:
            value = self.value_type(value)
        except (ValueError, TypeError):
            raise exceptions.ValidateError("value_type declared does not match with provided value's type",
                                           self.value_type, type(value))
        return value

    def validate(self, value) -> typing.Union[exceptions.ValidateError, None]:
        """Inherited method that can be used in child-classes for additional input value validation"""
        return None

    def _formatted_input(self):
        if self.hint:
            return input(f"{utils.format_str(self.label, utils.TerminalColors.BOLD)} "
                         f"({self.hint}): ")
        return input(f"{utils.format_str(self.label, utils.TerminalColors.BOLD)}: ")

    @_Field.value.setter
    def value(self, value):
        value = self._convert_type(value)
        e = self.validate(value)
        if e is None:
            self._value = value
        else:
            raise e

    def render(self):
        value_changed = False
        while not value_changed:
            try:
                v = self._formatted_input()
                self.value = v
                value_changed = True
            except exceptions.ValidateError as ex:
                print(utils.format_str(ex.__str__(), utils.TerminalColors.RED))
                pass


class OutputField(_Field):
    value_type = str

    def render(self):
        return f"{self.label}: {self.value}" if self.label else f"{self.value}"


class _NumericField(_InputField):
    min_value: float
    max_value: float

    def __init__(self, label: str, max_value: float = None, min_value: float = None,
                 hint: str = None):
        self.min_value = min_value
        self.max_value = max_value

        if self.min_value > self.max_value:
            self.min_value = self.max_value - 2

        super().__init__(label, hint)

    def _formatted_input(self):
        s = f"{utils.format_str(self.label, utils.TerminalColors.BOLD)} " + "({}): "
        ad = []

        if self.hint:
            ad.append(f"{self.hint}, ")

        if self.min_value and not self.max_value:
            ad.append(f'>{self.min_value}')

        elif self.max_value and not self.min_value or (self.max_value and self.min_value and self.max_value == 0):
            ad.append(f"<{self.max_value}")

        elif self.min_value and self.max_value:
            ad.append(f"{self.min_value} < n < {self.max_value}")

        while len(ad) != 2:
            ad.append('')

        return input(s.format(*ad))

    def validate(self, value) -> typing.Union[exceptions.ValidateError, None]:
        if self.min_value and not self.max_value:
            if not self.min_value < value:
                return exceptions.ValidateError("min_value = {}, input = {}".format(self.min_value, value))
        elif self.max_value and not self.min_value:
            if not self.max_value > value:
                return exceptions.ValidateError('max_value = {}, input = {}'.format(self.max_value, value))
        elif self.max_value and self.min_value:
            if not self.min_value < value < self.max_value:
                return exceptions.ValidateError('{} < {} < {} != True'.format(self.min_value, value, self.max_value))

        return super().validate(value)


class IntegerField(_NumericField):
    value_type = int


class FloatField(_NumericField):
    value_type = float
    mantissa: int

    def __init__(self, label: str, mantissa: int = 2, max_value: float = None, min_value: float = None,
                 hint: str = None, ):
        super().__init__(label=label, hint=hint, min_value=min_value, max_value=max_value)
        self.mantissa = mantissa

    @_InputField.value.getter
    def value(self):
        return round(self._value, self.mantissa)


class StringField(_InputField):
    """Simple field accepting strings"""
    value_type = str

    _input_callable = input

    def __init__(self, label: str, hint: str = None, max_length: int = _DEFAULT_MAX_LENGTH):
        self.max_length = max_length
        super().__init__(label, hint)

    def validate(self, value) -> typing.Union[exceptions.ValidateError, None]:
        if self.max_length:
            if len(str(value)) > self.max_length:
                return exceptions.ValidateError('max_length has been exceeded', self.max_length)
        return super().validate(value)

    def _formatted_input(self):
        if self.hint and self.max_length:
            return self._input_callable(f"{utils.format_str(self.label, utils.TerminalColors.BOLD)} "
                         f"({self.hint}, max. {self.max_length}): ")

        if self.hint:
            return self._input_callable(f"{utils.format_str(self.label, utils.TerminalColors.BOLD)} "
                         f"({self.hint}): ")
        elif self.max_length:
            return self._input_callable(f"{utils.format_str(self.label, utils.TerminalColors.BOLD)} (max. {self.max_length}): ")

        return self._input_callable(f"{utils.format_str(self.label, utils.TerminalColors.BOLD)}: ")


class HashedField(StringField):
    """Returns a hashed string instead of raw input value"""

    @StringField.value.getter
    def value(self):
        return hash(self._value)


class EmailField(StringField):

    def validate(self, value) -> typing.Union[exceptions.ValidateError, None]:
        r = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
        if not re.fullmatch(r, value):
            return exceptions.ValidateError("can't extract email from string ", value)
        return super().validate(value)


class PhoneNumberField(StringField):

    def validate(self, value) -> typing.Union[exceptions.ValidateError, None]:
        r = r"^\+((?:9[679]|8[035789]|6[789]|5[90]|42|3[578]|2[1-689])|9[0-58]|8[1246]|6[0-6]|5[1-8]|4[013-9]|" \
            r"3[0-469]|2[70]|7|1)(?:\W*\d){0,13}\d$"

        if not re.fullmatch(r, value):
            return exceptions.ValidateError("can't extract phone number from string", value)
        return super().validate(value)


class DateField(_InputField):
    value_type = datetime.datetime
    format_string = '%d.%m.%Y'

    earlier_than: datetime.datetime
    later_than: datetime.datetime

    def __init__(self, label: str, earlier_than: datetime.datetime = None, later_than: datetime.datetime = None,
                 hint: str = None):
        super().__init__(label, hint)
        self.earlier_than, self.later_than = earlier_than, later_than

        if self.earlier_than and self.later_than:
            if not self.later_than < self.earlier_than:
                raise ValueError('later_than value should be smaller than earlier_than',
                                 self.earlier_than, self.later_than)

    def validate(self, value) -> typing.Union[exceptions.ValidateError, None]:
        earlier_than_f = self.earlier_than.strftime(self.format_string) if self.earlier_than else ''
        later_than_f = self.later_than.strftime(self.format_string) if self.later_than else ''

        if self.earlier_than and not self.later_than:
            if not value < self.earlier_than:
                return exceptions.ValidateError(f'should be earlier than {earlier_than_f}')

        elif self.later_than and not self.earlier_than:
            if not value > self.later_than:
                return exceptions.ValidateError(f'should be later than {later_than_f}')

        elif self.later_than and self.earlier_than:
            if not self.later_than < value < self.earlier_than:
                return exceptions.ValidateError(
                    f'should be later than {later_than_f} and earlier than {earlier_than_f}')

        return super().validate(value)

    def _formatted_input(self):
        label = f"{utils.format_str(self.label, utils.TerminalColors.BOLD)} - {self.format_string} "
        if self.hint:
            return input(label + f"({self.hint}): ")

        else:
            if self.earlier_than and not self.later_than:
                return input(label + f"(< {self.earlier_than.strftime(self.format_string)}): ")

            elif self.later_than and not self.earlier_than:
                return input(label + f"(> {self.earlier_than.strftime(self.format_string)}): ")

            elif self.later_than and self.earlier_than:
                return input(label + f"({self.later_than.strftime(self.format_string)} "
                                     f"< n < {self.earlier_than.strftime(self.format_string)}): ")

        return input(label + ": ")

    def _convert_type(self, value):
        try:
            value = datetime.datetime.strptime(value, self.format_string)
        except (ValueError, TypeError):
            raise exceptions.ValidateError("can't parse datetime from string",
                                           value, self.format_string)
        return value
