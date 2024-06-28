import struct
from typing import Callable, Union

import numpy as np

from src.wasm.type.numpy.base import NumpyNumericType
from src.wasm.type.numpy.int import I32


def fallback_glibc(fallback_func: Callable):
    glibc = np.signbit(np.minimum(np.float32(-0.0), np.float32(0.0)))

    def decorator(func: Callable):
        def wrapper(self: NumpyNumericType, other: NumpyNumericType):
            if glibc:
                return fallback_func(self, other)
            else:
                return func(self, other)

        return wrapper

    return decorator


class FloatFallbackType(NumpyNumericType):
    def __init__(self, value: np.float32):
        self.value = value

    def fallback_glibc_min(self, other: "FloatFallbackType"):
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

    def fallback_glibc_max(self, other: "FloatFallbackType"):
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


class FloatType(NumpyNumericType):
    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    def __floor__(self):
        return self.__class__.from_value(np.floor(self.value))

    def __ceil__(self):
        return self.__class__.from_value(np.ceil(self.value))

    def __trunc__(self):
        return self.__class__.from_value(np.trunc(self.value))

    def __round__(self):
        return self.__class__.from_value(np.round(self.value))

    @fallback_glibc(FloatFallbackType.fallback_glibc_min)
    def min(self, other: "FloatType"):
        return super().min(other)

    @fallback_glibc(FloatFallbackType.fallback_glibc_max)
    def max(self, other: "FloatType"):
        return super().max(other)


class F32(FloatType):
    def __init__(self, value: np.float32):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.float32))

    @classmethod
    def from_int(cls, value: Union[int, float]):
        return cls(np.float32(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        if value == "nan:canonical":
            return cls(np.float32(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float32(np.nan))
        else:
            bytes_value = struct.pack("I", int(value))
            return cls.from_bits(bytes_value)

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.float32)[0])

    def to_bits(self) -> bytes:
        return self.value.tobytes()

    @classmethod
    def get_length(cls):
        return 32


class F64(FloatType):
    def __init__(self, value: np.float64):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.float64))

    @classmethod
    def from_int(cls, value: Union[int, float]):
        return cls(np.float64(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        if value == "nan:canonical":
            return cls(np.float64(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float64(np.nan))
        else:
            bytes_value = struct.pack("Q", int(value))
            return cls.from_bits(bytes_value)

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.float64)[0])

    def to_bits(self) -> bytes:
        return self.value.tobytes()

    @classmethod
    def get_length(cls):
        return 64
