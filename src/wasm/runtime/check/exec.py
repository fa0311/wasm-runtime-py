from src.wasm.runtime.check.check import TypeCheck
from src.wasm.runtime.check.code_exec import CodeSectionBlockDebug
from src.wasm.runtime.error.error import (
    WasmCallStackExhaustedError,
)
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.numeric.base import NumericType


class WasmExecRelease(WasmExec):
    def run(self, index: int, param: list[NumericType]):
        return super().run(index, param)


class WasmExecCheck(WasmExec):
    def run(self, index: int, param: list[NumericType]):
        fn, fn_type = self.get_function(index)
        TypeCheck.type_check(param, fn_type.params)

        try:
            block, returns = super().run(index, param)
        except RecursionError:
            raise WasmCallStackExhaustedError()

        TypeCheck.type_check(returns, fn_type.returns)
        return block, returns

    def get_block(self, locals: list[NumericType], stack: list[NumericType]):
        return CodeSectionBlockDebug(
            env=self,
            locals=locals,
            stack=NumericStack(value=stack),
        )
