class NumericType:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value)

    @classmethod
    def from_int(cls, value):
        return cls(value)

    def to_signed(self):
        return SignedNumericType(self.value)

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
        return self.__class__.from_value(self.value == other.value)

    def __ne__(self, other: "NumericType"):
        return self.__class__.from_value(self.value != other.value)

    def __lt__(self, other: "NumericType"):
        return self.__class__.from_value(self.value < other.value)

    def __le__(self, other: "NumericType"):
        return self.__class__.from_value(self.value <= other.value)

    def __and__(self, other: "NumericType"):
        return self.__class__.from_value(self.value & other.value)

    def __or__(self, other: "NumericType"):
        return self.__class__.from_value(self.value | other.value)

    def __xor__(self, other: "NumericType"):
        return self.__class__.from_value(self.value ^ other.value)

    def __lshift__(self, other: "NumericType"):
        return self.__class__.from_value(self.value << other.value)

    def __rshift__(self, other: "NumericType"):
        return self.__class__.from_value(self.value >> other.value)

    def clz(self):
        if self.value == 0:
            return self.__class__.from_int(32)
        data = bin(self.value)[2:].zfill(32)
        return self.__class__.from_int(data.index("1"))

    def ctz(self):
        if self.value == 0:
            return self.__class__.from_int(32)
        data = bin(self.value)[2:].zfill(32)
        return self.__class__.from_int(data[::-1].index("1"))

    def popcnt(self):
        return self.__class__.from_int(bin(self.value).count("1"))


class SignedNumericType(NumericType):
    def to_unsigned(self):
        return self.__class__(self.value)
