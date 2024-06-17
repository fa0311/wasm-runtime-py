import numpy as np

from src.wasm.type.base import NumericType, SignedNumericType


class I32(NumericType):
    def __init__(self, value: np.uint32):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.uint32))

    @classmethod
    def from_int(cls, value):
        return cls(np.uint32(value))

    def to_signed(self):
        return SignedI32.from_int(self.value.astype(np.int32))

    def __mod__(self, other: "NumericType"):
        return self.__class__.from_value(np.remainder(self.value, other.value))


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

    def __floordiv__(self, other: "NumericType"):
        result = self.value / other.value
        return self.__class__.from_value(np.floor(result))

    def __mod__(self, other: "NumericType"):
        result = self.value - other.value * (self / other).value
        return self.__class__.from_value(result)


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
