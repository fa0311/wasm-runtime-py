from typing import Union

import numpy as np

from src.wasm.type.numpy.base import NumpyNumericType


class UnsignedIntType(NumpyNumericType):
    """符号なし整数型の基底クラス"""

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    @classmethod
    def get_min(cls):
        return 0

    @classmethod
    def get_max(cls):
        return (2 ** cls.get_length()) - 1

    def __truediv__(self, other: "UnsignedIntType"):
        return self.__floordiv__(other)


class SignedIntType(NumpyNumericType):
    """符号付き整数型の基底クラス"""

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    def __truediv__(self, other: "SignedIntType"):
        return self.__floordiv__(other)

    def __floordiv__(self, other: "SignedIntType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        return self.__class__.from_value(a + c.value)

    def __mod__(self, other: "SignedIntType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        result = self.value - (other.value * (a + c.value))
        return self.__class__.from_value(result)


class I8(UnsignedIntType):
    """8bit符号なし整数型"""

    def __init__(self, value: np.uint8):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.uint8))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint8(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint8(int(value)))

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.uint8)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<u1")

    @classmethod
    def get_length(cls):
        return 8


class I16(UnsignedIntType):
    """16bit符号なし整数型"""

    def __init__(self, value: np.uint16):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.uint16))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint16(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint16(int(value)))

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.uint16)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<u2")

    @classmethod
    def get_length(cls):
        return 16


class I32(UnsignedIntType):
    """32bit符号なし整数型"""

    def __init__(self, value: np.uint32):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.uint32))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint32(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint32(int(value)))

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.uint32)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<u4")

    @classmethod
    def get_length(cls):
        return 32

    def __repr__(self):
        cls_name = self.__class__.__name__
        cls_value = I32.astype(self)
        return f"{cls_name}(value={cls_value.value})"


class I64(UnsignedIntType):
    """64bit符号なし整数型"""

    def __init__(self, value: np.uint64):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.uint64))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint64(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint64(int(value)))

    @classmethod
    def get_length(cls):
        return 64

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.uint64)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<u8")

    def __repr__(self):
        cls_name = self.__class__.__name__
        cls_value = I64.astype(self)
        return f"{cls_name}(value={cls_value.value})"


class SignedI8(SignedIntType):
    """8bit符号付き整数型"""

    def __init__(self, value: np.int8):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.int8))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int8(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int8(int(value)))

    @classmethod
    def get_length(cls):
        return 8

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.int8)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<i1")


class SignedI16(SignedIntType):
    """16bit符号付き整数型"""

    def __init__(self, value: np.int16):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.int16))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int16(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int16(int(value)))

    @classmethod
    def get_length(cls):
        return 16

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.int16)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<i2")


class SignedI32(SignedIntType):
    """32bit符号付き整数型"""

    def __init__(self, value: np.int32):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.int32))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int32(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int32(int(value)))

    @classmethod
    def get_length(cls):
        return 32

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.int32)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<i4")


class SignedI64(SignedIntType):
    """64bit符号付き整数型"""

    def __init__(self, value: np.int64):
        self.value = value

    @classmethod
    def astype(cls, value: NumpyNumericType):
        return cls(value.value.astype(np.int64))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int64(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int64(int(value)))

    @classmethod
    def get_length(cls):
        return 64

    @classmethod
    def from_bits(cls, bytes_value: bytes):
        return cls(np.frombuffer(bytes_value, dtype=np.int64)[0])

    def to_bits(self) -> bytes:
        return self.value.view("<i8")


class LEB128(NumpyNumericType):
    def __init__(self, value):
        self.value = value
