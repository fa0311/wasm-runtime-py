from typing import Union

import numpy as np

from src.wasm.type.base import NumericType, SignedNumericType, UnsignedNumericType


class UnsignedIntType(UnsignedNumericType):
    """符号なし整数型の基底クラス"""

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    def __truediv__(self, other: NumericType):
        return self.__floordiv__(other)

    def __repr__(self):
        cls_name = self.__class__.__name__
        cls_value = self.value
        return f"{cls_name}({cls_value})"


class I8(UnsignedIntType):
    """8bit符号なし整数型"""

    def __init__(self, value: np.uint8):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.uint8))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint8(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint8(int(value)))

    @classmethod
    def get_length(cls):
        return 8

    def to_signed(self):
        return SignedI8.from_value(self.value)


class I16(UnsignedIntType):
    """16bit符号なし整数型"""

    def __init__(self, value: np.uint16):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.uint16))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint16(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint16(int(value)))

    @classmethod
    def get_length(cls):
        return 16

    def to_signed(self):
        return SignedI16.from_value(self.value)


class I32(UnsignedIntType):
    """32bit符号なし整数型"""

    def __init__(self, value: np.uint32):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.uint32))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint32(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint32(int(value)))

    @classmethod
    def get_length(cls):
        return 32

    def to_signed(self):
        return SignedI32.from_value(self.value)


class I64(UnsignedIntType):
    """64bit符号なし整数型"""

    def __init__(self, value: np.uint64):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.uint64))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.uint64(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.uint64(int(value)))

    @classmethod
    def get_length(cls):
        return 64

    def to_signed(self):
        return SignedI64.from_value(self.value)


class SignedIntType(SignedNumericType):
    """符号付き整数型の基底クラス"""

    @classmethod
    def from_bool(cls, value: bool):
        return I32.from_int(1 if value else 0)

    def __truediv__(self, other: NumericType):
        return self.__floordiv__(other)

    def __floordiv__(self, other: "NumericType"):
        a, b = np.divmod(self.value, other.value)
        c = self.__class__.from_bool(a < 0 and b != 0)
        return self.__class__.from_value(a + c.value)

    def __mod__(self, other: "NumericType"):
        result = self.value - other.value * (self // other).value
        return self.__class__.from_value(result)

    def __repr__(self):
        cls_name = self.__class__.__name__
        cls_value = self.to_unsigned().value
        return f"{cls_name}({cls_value})"


class SignedI8(SignedIntType):
    """8bit符号付き整数型"""

    def __init__(self, value: np.int8):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.int8))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int8(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int8(int(value)))

    @classmethod
    def get_length(cls):
        return 8

    def to_unsigned(self):
        return I8.from_value(self.value)


class SignedI16(SignedIntType):
    """16bit符号付き整数型"""

    def __init__(self, value: np.int16):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.int16))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int16(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int16(int(value)))

    @classmethod
    def get_length(cls):
        return 16

    def to_unsigned(self):
        return I16.from_value(self.value)


class SignedI32(SignedIntType):
    """32bit符号付き整数型"""

    def __init__(self, value: np.int32):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.int32))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int32(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int32(int(value)))

    @classmethod
    def get_length(cls):
        return 32

    def to_unsigned(self):
        return I32.from_value(self.value)


class SignedI64(SignedIntType):
    """64bit符号付き整数型"""

    def __init__(self, value: np.int64):
        self.value = value

    @classmethod
    def from_value(cls, value: np.generic):
        return cls(value.astype(np.int64))

    @classmethod
    def from_int(cls, value: int):
        return cls(np.int64(value))

    @classmethod
    def from_str(cls, value: Union[str, bytes]):
        return cls(np.int64(int(value)))

    @classmethod
    def get_length(cls):
        return 64

    def to_unsigned(self):
        return I64.from_value(self.value)


class LEB128(NumericType):
    def __init__(self, value):
        self.value = value
