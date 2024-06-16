from src.wasm.type.base import NumericType, SignedNumericType


class I32(NumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def truncate(cls, value):
        return cls(value % (2**32))

    def to_signed(self):
        return SignedI32.truncate(self.value if self.value < 2**31 else self.value - 2**32)


class SignedI32(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def truncate(cls, value):
        return cls(value)

    def __truediv__(self, other: "SignedI32"):
        res = self.value / other.value
        return self.__class__.truncate(int(res))

    def __mod__(self, other: "SignedI32"):
        return self.__class__.truncate(abs(self.value % other.value))

    def to_unsigned(self):
        return I32.truncate(self.value if self.value >= 0 else self.value + 2**32)


class I64(NumericType):
    def __init__(self, value):
        self.value = value


class F32(NumericType):
    def __init__(self, value):
        self.value = value


class F64(NumericType):
    def __init__(self, value):
        self.value = value


class LEB128(NumericType):
    def __init__(self, value):
        self.value = value
