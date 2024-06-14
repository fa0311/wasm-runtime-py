class NumericType:
    def __init__(self, value):
        self.value = value

    @classmethod
    def truncate(cls, value):
        return cls(value)

    def to_signed(self):
        return SignedNumericType(self.value)

    def __add__(self, other: "NumericType"):
        return self.__class__.truncate(self.value + other.value)

    def __sub__(self, other: "NumericType"):
        return self.__class__.truncate(self.value - other.value)

    def __mul__(self, other: "NumericType"):
        return self.__class__.truncate(self.value * other.value)

    def __truediv__(self, other: "NumericType"):
        return self.__class__.truncate(self.value // other.value)

    def __mod__(self, other: "NumericType"):
        return self.__class__.truncate(self.value % other.value)

    def __eq__(self, other: "NumericType"):
        return self.__class__.truncate(self.value == other.value)

    def __ne__(self, other: "NumericType"):
        return self.__class__.truncate(self.value != other.value)

    def __lt__(self, other: "NumericType"):
        return self.__class__.truncate(self.value < other.value)

    def __le__(self, other: "NumericType"):
        return self.__class__.truncate(self.value <= other.value)

    def __and__(self, other: "NumericType"):
        return self.__class__.truncate(self.value & other.value)

    def __or__(self, other: "NumericType"):
        return self.__class__.truncate(self.value | other.value)

    def __xor__(self, other: "NumericType"):
        return self.__class__.truncate(self.value ^ other.value)


class SignedNumericType(NumericType):
    def to_unsigned(self):
        return self.__class__(self.value)


class LEB128(NumericType):
    def __init__(self, value):
        self.value = value


class I32(NumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def truncate(cls, value):
        return cls(value % (2**32))

    def to_signed(self):
        return SignedI32(self.value if self.value < 2**31 else self.value - 2**32)


class SignedI32(SignedNumericType):
    def __init__(self, value):
        self.value = value

    def __truediv__(self, other: "SignedI32"):
        if self.value < 0 and other.value > 0 and self.value % other.value != 0:
            return self.__class__(self.value // other.value + 1)
        else:
            return self.__class__(self.value // other.value)

    def to_unsigned(self):
        return I32(self.value if self.value >= 0 else self.value + 2**32)


class I64(NumericType):
    def __init__(self, value):
        self.value = value % (2**64)


class F32(NumericType):
    def __init__(self, value):
        self.value = value


class F64(NumericType):
    def __init__(self, value):
        self.value = value
