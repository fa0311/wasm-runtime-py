import struct
from typing import Union

import numpy as np

from src.wasm.type.numeric.numpy.base import NumpyNumericType
from src.wasm.type.numeric.numpy.int import I32


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

    def min(self, other: "FloatType"):
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

    def max(self, other: "FloatType"):
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


class F32(FloatType):
    def __init__(self, value: np.float32):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.float32))

    @classmethod
    def from_int(cls, value: Union[int, float]):
        x = np.float32(value)
        return cls(x)

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        if value == "nan:canonical":
            return cls(np.float32(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float32(np.inf))
        else:
            bytes_value = struct.pack("I", int(value))
            return cls.from_bits(bytes_value)

    @classmethod
    def from_bits(cls, bytes_value: Union[bytes, np.ndarray]):
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
        x = np.float64(value)
        return cls(x)

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        if value == "nan:canonical":
            return cls(np.float64(np.nan))
        elif value == "nan:arithmetic":
            return cls(np.float64(np.inf))
        else:
            bytes_value = struct.pack("Q", int(value))
            return cls.from_bits(bytes_value)

    @classmethod
    def from_bits(cls, bytes_value: Union[bytes, np.ndarray]):
        return cls(np.frombuffer(bytes_value, dtype=np.float64)[0])

    def to_bits(self) -> bytes:
        return self.value.tobytes()

    @classmethod
    def get_length(cls):
        return 64
