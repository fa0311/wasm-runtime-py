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

    @classmethod
    def get_length(cls):
        return 32

    @classmethod
    def from_bool(cls, value):
        return cls(np.uint32(1 if value else 0))

    def to_signed(self):
        return SignedI32.from_value(self.value)


class SignedI32(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.int32))

    @classmethod
    def from_int(cls, value):
        return cls(np.int32(value))

    @classmethod
    def get_length(cls):
        return 32

    @classmethod
    def from_bool(cls, value):
        return cls(np.uint32(1 if value else 0))

    def to_unsigned(self):
        return I32.from_value(self.value)

    def __floordiv__(self, other: "NumericType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        return self.__class__.from_value(a + c.value)

    def __mod__(self, other: "NumericType"):
        result = self.value - other.value * (self // other).value
        return self.__class__.from_value(result)


class I64(NumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.uint64))

    @classmethod
    def from_int(cls, value):
        return cls(np.uint64(value))

    @classmethod
    def get_length(cls):
        return 64

    @classmethod
    def from_bool(cls, value):
        return cls(np.uint32(1 if value else 0))

    def to_signed(self):
        return SignedI64.from_value(self.value)


class SignedI64(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.int64))

    @classmethod
    def from_int(cls, value):
        return cls(np.int64(value))

    @classmethod
    def get_length(cls):
        return 64

    @classmethod
    def from_bool(cls, value):
        return cls(np.uint32(1 if value else 0))

    def to_unsigned(self):
        return I64.from_value(self.value)

    def __floordiv__(self, other: "NumericType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        return self.__class__.from_value(a + c.value)

    def __mod__(self, other: "NumericType"):
        result = self.value - other.value * (self // other).value
        return self.__class__.from_value(result)


class F32(NumericType):
    def __init__(self, value):
        self.value = value


class F64(NumericType):
    def __init__(self, value):
        self.value = value


class LEB128(NumericType):
    def __init__(self, value):
        self.value = value
