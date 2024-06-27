import numpy as np

from src.wasm.type.base import NumericType


class NumpyNumericType(NumericType):
    def __init__(self, value: np.number):
        self.value = value

    def sqrt(self):
        return self.__class__.from_value(np.sqrt(self.value))

    def copysign(self, other: "NumpyNumericType"):
        return self.__class__.from_value(np.copysign(self.value, other.value))

    def min(self, other: "NumpyNumericType"):
        return self.__class__.from_value(np.minimum(self.value, other.value))

    def max(self, other: "NumpyNumericType"):
        return self.__class__.from_value(np.maximum(self.value, other.value))

    def clamp(self, min: "NumpyNumericType", max: "NumpyNumericType"):
        return self.__class__.from_value(np.clip(self.value, min.value, max.value))
