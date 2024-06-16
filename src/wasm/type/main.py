import numpy as np

from src.wasm.type.base import NumericType, SignedNumericType


class I32(NumericType):
    def __init__(self, value):
        self.value = np.uint32(value)

    @classmethod
    def truncate(cls, value):
        return cls(np.uint32(value))

    def to_signed(self):
        return SignedI32(self.value.astype(np.int32))

    def __lshift__(self, other: NumericType):
        return self.__class__.truncate(self.value << other.value)

    def clz(self):
        """先頭ビットから数えて連続した0の数"""
        # bin ha 0bxxxx で始まるので2文字目から
        # bin ha 可変長だとバグるので32文字に固定
        if self.value == 0:
            return self.__class__.truncate(32)
        data = bin(self.value)[2:].zfill(32)
        return self.__class__.truncate(data.index("1"))

    def ctz(self):
        """末尾ビットから数えて連続した0の数"""
        if self.value == 0:
            return self.__class__.truncate(32)
        data = bin(self.value)[2:].zfill(32)
        return self.__class__.truncate(data[::-1].index("1"))

    def popcnt(self):
        return self.__class__.truncate(bin(self.value).count("1"))


class SignedI32(SignedNumericType):
    def __init__(self, value):
        self.value = value

    @classmethod
    def truncate(cls, value):
        return cls(np.int32(value))

    def to_unsigned(self):
        return I32(self.value.astype(np.uint32))


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
