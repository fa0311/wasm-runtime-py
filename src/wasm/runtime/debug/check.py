from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.type.base import NumericType


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
            raise Exception("invalid param length")
        for a, b in zip(param, params_type):
            if a.__class__ != WasmOptimizer.get_type(b):
                raise Exception(f"invalid return type {a.__class__} != {WasmOptimizer.get_type(b)}")
