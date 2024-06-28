import numpy as np

from src.wasm.type.base import NumericType


class NumpyNumericType(NumericType):
    def __init__(self, value: np.number):
        self.value = value

    @classmethod
    def from_value_with_clamp(cls, value: "NumpyNumericType", clamp: type["NumpyNumericType"]) -> "NumpyNumericType":
        min_value = value.__class__.from_int(clamp.get_min())
        max_value = value.__class__.from_int(clamp.get_max())

        if np.isnan(value.value):
            return cls.from_int(0)
        if np.isinf(value.value):
            if np.signbit(value.value):
                return cls.from_int(clamp.get_min())
            else:
                return cls.from_int(clamp.get_max())

        if value.value <= min_value.value:
            return cls.from_int(clamp.get_min())
        if value.value >= max_value.value:
            return cls.from_int(clamp.get_max())
        return cls.from_value(value.value)

    def sqrt(self):
        return self.__class__.from_value(np.sqrt(self.value))

    def copysign(self, other: "NumpyNumericType"):
        return self.__class__.from_value(np.copysign(self.value, other.value))

    def min(self, other: "NumpyNumericType"):
        return self.__class__.from_value(np.minimum(self.value, other.value))

    def max(self, other: "NumpyNumericType"):
        return self.__class__.from_value(np.maximum(self.value, other.value))

    def is_nan(self):
        return np.isnan(self.value)
