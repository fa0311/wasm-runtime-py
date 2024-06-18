from typing import Union


class NumericType:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value)

    @classmethod
    def from_int(cls, value: int):
        return cls(value)

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(int(value))

    @classmethod
    def from_bool(cls, value: bool):
        return cls(1 if value else 0)

    @classmethod
    def get_length(cls):
        return 32

    def __add__(self, other: "NumericType"):
        return self.__class__.from_value(self.value + other.value)

    def __sub__(self, other: "NumericType"):
        return self.__class__.from_value(self.value - other.value)

    def __mul__(self, other: "NumericType"):
        return self.__class__.from_value(self.value * other.value)

    def __truediv__(self, other: "NumericType"):
        return self.__class__.from_value(self.value / other.value)

    def __floordiv__(self, other: "NumericType"):
        return self.__class__.from_value(self.value // other.value)

    def __mod__(self, other: "NumericType"):
        return self.__class__.from_value(self.value % other.value)

    def __eq__(self, other: "NumericType"):
        return self.__class__.from_bool(self.value == other.value)

    def __ne__(self, other: "NumericType"):
        return self.__class__.from_bool(self.value != other.value)

    def __lt__(self, other: "NumericType"):
        return self.__class__.from_bool(self.value < other.value)

    def __le__(self, other: "NumericType"):
        return self.__class__.from_bool(self.value <= other.value)

    def __and__(self, other: "NumericType"):
        return self.__class__.from_value(self.value & other.value)

    def __or__(self, other: "NumericType"):
        return self.__class__.from_value(self.value | other.value)

    def __xor__(self, other: "NumericType"):
        return self.__class__.from_value(self.value ^ other.value)

    def __rshift__(self, other: "NumericType"):
        length = self.__class__.from_int(self.__class__.get_length())
        return self.__class__.from_value(self.value >> (other.value % length.value))

    def __lshift__(self, other: "NumericType"):
        length = self.__class__.from_int(self.__class__.get_length())
        return self.__class__.from_value(self.value << (other.value % length.value))

    def __ceil__(self):
        return self.__class__.from_value(self.value.__ceil__())

    def __floor__(self):
        return self.__class__.from_value(self.value.__floor__())

    def __trunc__(self):
        return self.__class__.from_value(self.value.__trunc__())

    def __round__(self):
        return self.__class__.from_value(self.value.__round__())

    def clz(self):
        if self.value == 0:
            return self.__class__.from_int(self.__class__.get_length())
        data = bin(self.value)[2:].zfill(self.__class__.get_length())
        return self.__class__.from_int(data.index("1"))

    def ctz(self):
        if self.value == 0:
            return self.__class__.from_int(self.__class__.get_length())
        data = bin(self.value)[2:].zfill(self.__class__.get_length())
        return self.__class__.from_int(data[::-1].index("1"))

    def popcnt(self):
        return self.__class__.from_int(bin(self.value).count("1"))

    def rotl(self, other: "NumericType"):
        length = self.__class__.from_int(self.__class__.get_length())
        return self << other | (self >> length - other)

    def rotr(self, other: "NumericType"):
        length = self.__class__.from_int(self.__class__.get_length())
        return self >> other | (self << length - other)

    def min(self, other: "NumericType"):
        return self if self.value < other.value else other

    def max(self, other: "NumericType"):
        return self if self.value > other.value else other

    def sqrt(self):
        return self.__class__.from_value(self.value**0.5)

    def to_signed(self):
        raise NotImplementedError

    def to_unsigned(self):
        raise NotImplementedError


class UnsignedNumericType(NumericType):
    def to_signed(self):
        return SignedNumericType(self.value)


class SignedNumericType(NumericType):
    def to_unsigned(self):
        return UnsignedNumericType(self.value)
