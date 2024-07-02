from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.error.error import WasmIntegerOverflowError, WasmInvalidConversionError
from src.wasm.type.base import NumericType


class TypeCheck:
    @staticmethod
    def type_check_1(value: NumericType, clamp: type[NumericType], raise_cls: type[NumericType]):
        """型チェックを行う"""
        min_value = value.__class__.from_int(clamp.get_min())
        max_value = value.__class__.from_int(clamp.get_max())

        if value.value < min_value.value:
            raise WasmIntegerOverflowError([raise_cls])

        import numpy as np

        if value.value == min_value.value:
            if not np.isclose(value.value, min_value.value):
                raise WasmIntegerOverflowError([raise_cls])

        if value.value > max_value.value:
            raise WasmIntegerOverflowError([raise_cls])

        # if np.isclose(value.value, max_value.value):
        #     raise WasmIntegerOverflowError([raise_cls])

    @staticmethod
    def type_check_2(value: NumericType, clamp: type[NumericType], raise_cls: type[NumericType]):
        """型チェックを行う"""
        min_value = value.__class__.from_int(clamp.get_min())
        max_value = value.__class__.from_int(clamp.get_max())

        import numpy as np

        if np.isnan(value.value):
            raise WasmInvalidConversionError([raise_cls])
        if np.isinf(value.value):
            if np.signbit(value.value):
                raise WasmIntegerOverflowError([raise_cls])
            else:
                raise WasmIntegerOverflowError([raise_cls])

        if value.value < min_value.value:
            raise WasmIntegerOverflowError([raise_cls])

        if value.value > max_value.value:
            raise WasmIntegerOverflowError([raise_cls])

        if value.value == max_value.value:
            raise WasmIntegerOverflowError([raise_cls])

    @staticmethod
    def type_check(param: list[NumericType], params_type: list[int]):
        if len(param) != len(params_type):
            raise Exception("invalid param length")
        for a, b in zip(param, params_type):
            if a.__class__ != WasmOptimizer.get_type(b):
                raise Exception(f"invalid return type {a.__class__} != {WasmOptimizer.get_type(b)}")
