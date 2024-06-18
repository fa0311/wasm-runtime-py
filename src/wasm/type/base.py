from typing import Callable


def catch_error(func: Callable):
    try:
        return func()
    except Exception:
        return None


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
    def from_str(cls, value: str):
        return cls(int(value))

    @classmethod
    def from_bool(cls, value: bool):
        return cls(1 if value else 0)

    @classmethod
    def get_length(cls):
        return 32

    def to_signed(self):
        return SignedNumericType(self.value)

    def __repr__(self):
        cls_name = self.__class__.__name__
        signed = catch_error(lambda: self.to_signed().value)
        return f"{cls_name}({self.value}, signed={signed}, floated={self.value:.32f})"

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

    # def __neg__(self):
    #     return self.__class__.from_value(-self.value)

    # def __invert__(self):
    #     return self.__class__.from_value(~self.value)

    # def __abs__(self):
    #     return self.__class__.from_value(abs(self.value))

    # def __pos__(self):
    #     return self.__class__.from_value(+self.value)

    # def __round__(self):
    #     return self.__class__.from_value(round(self.value))

    # def __pow__(self, other: "NumericType"):
    #     return self.__class__.from_value(self.value**other.value)

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


class SignedNumericType(NumericType):
    def to_unsigned(self):
        return self.__class__(self.value)
