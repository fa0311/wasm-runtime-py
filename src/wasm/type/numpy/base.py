import numpy as np

from src.wasm.type.base import NumericType


class NumpyNumericType(NumericType):
    def __init__(self, value: np.generic):
        self.value = value

    def sqrt(self):
        return self.__class__.from_value(np.sqrt(self.value))

    def copysign(self, other: "NumericType"):
        return self.__class__.from_value(np.copysign(self.value, other.value))
