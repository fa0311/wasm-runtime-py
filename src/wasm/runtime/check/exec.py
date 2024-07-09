from src.wasm.runtime.check.check import TypeCheck
from src.wasm.runtime.check.code_exec import CodeSectionBlockDebug
from src.wasm.runtime.error.error import (
    WasmCallStackExhaustedError,
)
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.base import AnyType


class WasmExecRelease(WasmExec):
    def run(self, index: int, param: list[AnyType]):
        return super().run(index, param)


class WasmExecCheck(WasmExec):
    def run(self, index: int, param: list[AnyType]):
        fn, fn_type = self.get_function(index)
        TypeCheck.type_check(param, fn_type.params)

        try:
            block, returns = super().run(index, param)
        except RecursionError:
            raise WasmCallStackExhaustedError()

        TypeCheck.type_check(returns, fn_type.returns)
        return block, returns

    def get_block(self, locals: list[AnyType], stack: list[AnyType]):
        return CodeSectionBlockDebug(
            env=self,
            locals=locals,
            stack=NumericStack(value=stack),
        )
