import struct

import numpy as np

from src.wasm.type.base import NumericType, SignedNumericType


class I32(NumericType):
    def __init__(self, value: np.uint32):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.uint32))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint32(value))

    @classmethod
    def from_str(cls, value: str):
        return cls(np.uint32(int(value)))

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    @classmethod
    def get_length(cls):
        return 32

    def to_signed(self):
        return SignedI32.from_value(self.value)

    def __floordiv__(self, other: NumericType):
        return self.__truediv__(other)


class SignedI32(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.int32))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int32(value))

    @classmethod
    def from_str(cls, value: str):
        return cls(np.int32(int(value)))

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    @classmethod
    def get_length(cls):
        return 32

    def to_unsigned(self):
        return I32.from_value(self.value)

    def __truediv__(self, other: "NumericType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        return self.__class__.from_value(a + c.value)

    def __floordiv__(self, other: NumericType):
        return self.__truediv__(other)

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
    def from_int(cls, value: int):
        return cls(np.uint64(value))

    @classmethod
    def from_str(cls, value: str):
        return cls(np.uint64(int(value)))

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    @classmethod
    def get_length(cls):
        return 64

    def to_signed(self):
        return SignedI64.from_value(self.value)

    def __floordiv__(self, other: NumericType):
        return self.__truediv__(other)


class SignedI64(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        return cls(value.astype(np.int64))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int64(value))

    @classmethod
    def from_str(cls, value: str):
        return cls(np.int64(int(value)))

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    @classmethod
    def get_length(cls):
        return 64

    def to_unsigned(self):
        return I64.from_value(self.value)

    def __truediv__(self, other: "NumericType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        return self.__class__.from_value(a + c.value)

    def __floordiv__(self, other: NumericType):
        return self.__truediv__(other)

    def __mod__(self, other: "NumericType"):
        result = self.value - other.value * (self // other).value
        return self.__class__.from_value(result)


class F32(NumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_value(cls, value):
        if np.isinf(value):
            return cls(np.float32(np.nan))
        else:
            return cls(value.astype(np.float32))

    @classmethod
    def from_int(cls, value: int):
        bytes_value = struct.pack("I", value)
        float_value = struct.unpack("f", bytes_value)[0]
        return cls(np.float32(float_value))

    @classmethod
    def from_str(cls, value: str):
        if value == "nan:canonical":
            return cls(np.float32(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float32(np.nan))
        else:
            bytes_value = struct.pack("I", int(value))
            float_value = struct.unpack("f", bytes_value)[0]
            return cls(np.float32(float_value))

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    @classmethod
    def get_length(cls):
        return cls(np.fmax)

    def to_signed(self):
        raise NotImplementedError

    def min(self, other: NumericType):
        if np.isnan(self.value) or np.isnan(other.value):
            return self.__class__(np.nan)
        else:
            return self.__class__.from_value(np.fmin(self.value, other.value))

    def max(self, other: NumericType):
        if np.isnan(self.value) or np.isnan(other.value):
            return self.__class__(np.nan)
        else:
            return self.__class__.from_value(np.fmax(self.value, other.value))


class F64(NumericType):
    def __init__(self, value):
        self.value = value


class LEB128(NumericType):
    def __init__(self, value):
        self.value = value
