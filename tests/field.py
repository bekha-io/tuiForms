import random
import unittest
from unittest.mock import patch

import exceptions
from fields import *


class TestStringField(unittest.TestCase):

    def setUp(self) -> None:
        self.f = StringField(label='TestField')

    def test_max_length_broken(self):
        self.f.max_length = 1
        self.assertRaises(exceptions.ValidateError, self.f.__setattr__, 'value', '123123')


class TestFloatField(unittest.TestCase):

    def setUp(self) -> None:
        self.f = FloatField(label='TestFloatField')

    def test_min_value_broken(self):
        self.f.min_value = 100
        self.assertRaises(exceptions.ValidateError, self.f.__setattr__, 'value', 60)

    def test_max_value_broken(self):
        self.f.min_value = 100
        self.f.max_value = 1000
        self.assertRaises(exceptions.ValidateError, self.f.__setattr__, 'value', 4000)

    def test_min_max_values_broken(self):
        self.f.min_value = 100
        self.f.max_value = 200
        self.assertRaises(exceptions.ValidateError, self.f.__setattr__, 'value', 1000)

    def test_mantissa(self):
        for i in range(1, 100):
            self.f.mantissa = random.randint(2, 5)
            self.f.value = random.uniform(1.5, 5.5)
            to_check = str(self.f.value).split('.')[-1]
            self.assertGreaterEqual(self.f.mantissa, len(to_check))


class TestDateField(unittest.TestCase):

    def setUp(self) -> None:
        self.f = DateField(label=self.__class__.__name__)