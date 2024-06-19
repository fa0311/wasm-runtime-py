import struct
from typing import Callable, Union

import numpy as np

from src.wasm.type.base import NumericType
from src.wasm.type.numpy.int import I32


def fallback_x87(fallback_func: Callable):
    x87 = np.signbit(np.minimum(np.float32(0.0), np.float32(-0.0)))

    def decorator(func: Callable):
        def wrapper(self: NumericType, other: NumericType):
            if x87:
                return fallback_func(self, other)
            else:
                return func(self, other)

        return wrapper

    return decorator


class FloatFallbackType(NumericType):
    def fallback_x87_min(self, other: NumericType):
        if np.isnan(self.value):
            return self
        elif np.isnan(other.value):
            return other
        elif self.value < other.value:
            return self
        elif self.value > other.value:
            return other
        elif np.signbit(self.value) and not np.signbit(other.value):
            return self
        elif not np.signbit(self.value) and np.signbit(other.value):
            return other
        else:
            return self

    def fallback_x87_max(self, other: NumericType):
        if np.isnan(self.value):
            return self
        elif np.isnan(other.value):
            return other
        elif self.value > other.value:
            return self
        elif self.value < other.value:
            return other
        elif not np.signbit(self.value) and np.signbit(other.value):
            return self
        elif np.signbit(self.value) and not np.signbit(other.value):
            return other
        else:
            return self


class FloatType(NumericType):
    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    def to_signed(self):
        raise NotImplementedError

    def __floor__(self):
        return self.__class__.from_value(np.floor(self.value))

    def __ceil__(self):
        return self.__class__.from_value(np.ceil(self.value))

    def __trunc__(self):
        return self.__class__.from_value(np.trunc(self.value))

    def __round__(self):
        return self.__class__.from_value(np.round(self.value))

    def sqrt(self):
        return self.__class__.from_value(np.sqrt(self.value))

    @fallback_x87(FloatFallbackType.fallback_x87_min)
    def min(self, other: NumericType):
        return self.__class__.from_value(np.minimum(self.value, other.value))

    @fallback_x87(FloatFallbackType.fallback_x87_max)
    def max(self, other: NumericType):
        return self.__class__.from_value(np.maximum(self.value, other.value))


class F32(FloatType):
    def __init__(self, value: np.float32):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.float32))

    @classmethod
    def from_int(cls, value: int):
        bytes_value = struct.pack("I", value)
        float_value = struct.unpack("f", bytes_value)[0]
        return cls(np.float32(float_value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        if value == "nan:canonical":
            return cls(np.float32(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float32(np.nan))
        else:
            return cls.from_int(int(value))

    @classmethod
    def get_length(cls):
        return 32


class F64(FloatType):
    def __init__(self, value: np.float64):
        self.value = value

    @classmethod
    def from_value(cls, value: np.float64):
        return cls(value.astype(np.float64))

    @classmethod
    def from_int(cls, value: int):
        bytes_value = struct.pack("Q", value)
        float_value = struct.unpack("d", bytes_value)[0]
        return cls(np.float64(float_value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        if value == "nan:canonical":
            return cls(np.float64(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float64(np.nan))
        else:
            return cls.from_int(int(value))

    @classmethod
    def get_length(cls):
        return 64
