import numpy as np

from src.wasm.type.base import NumericType, SignedNumericType


class I32(NumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.uint32))

    @classmethod
    def from_int(cls, value):
        return cls(np.uint32(value))

    def to_signed(self):
        return SignedI32.from_int(self.value.astype(np.int32))

    def __lshift__(self, other: NumericType):
        return self.__class__.from_value(self.value << other.value)

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


class SignedI32(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.int32))

    @classmethod
    def from_int(cls, value):
        return cls(np.int32(value))

    def to_unsigned(self):
        return I32.from_int(self.value.astype(np.uint32))


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
