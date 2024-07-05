from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.type.numeric.base import NumericType


class TypeCheck:
    @staticmethod
    def cast_check(value: NumericType, clamp: type[NumericType]):
        """キャストが可能かチェックする"""
        min_value = value.__class__.from_int(clamp.get_min())
        max_value = value.__class__.from_int(clamp.get_max() + 1)

        if value.isnan():
            raise FloatingPointError()

        if value.isinf():
            raise FloatingPointError()

        if value.value < min_value.value:
            raise FloatingPointError()

        if value.value > max_value.value:
            raise FloatingPointError()

        if value.value == max_value.value:
            raise FloatingPointError()

    @staticmethod
    def type_check(param: list[NumericType], params_type: list[int]):
        if len(param) != len(params_type):
            raise TypeError("invalid param length")
        for a, b in zip(param, params_type):
            aa, bb = a.__class__, WasmOptimizer.get_type(b)
            if aa != bb:
                raise TypeError(f"invalid return type {aa} != {bb}")

    @staticmethod
    def list_check(a: list, b: list):
        if len(a) != len(b):
            raise TypeError("invalid length")
        for a, b in zip(a, b):
            if a != b:
                raise TypeError(f"invalid value {a} != {b}")

    if not __debug__:
        type_check = lambda *args, **kwargs: None  # noqa: E731
        list_check = lambda *args, **kwargs: None  # noqa: E731
