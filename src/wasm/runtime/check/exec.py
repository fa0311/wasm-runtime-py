from src.wasm.optimizer.struct import CodeInstructionOptimize
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
            returns = super().run(index, param)
        except RecursionError:
            raise WasmCallStackExhaustedError()

        TypeCheck.type_check(returns, fn_type.returns)
        return returns

    def run_data_int(self, data: list[CodeInstructionOptimize]):
        try:
            returns = super().run_data_int(data)
        except RecursionError:
            raise WasmCallStackExhaustedError()
        return returns

    def get_block(self, locals: list[AnyType], stack: list[AnyType]):
        return CodeSectionBlockDebug(
            env=self,
            locals=locals,
            stack=NumericStack(value=stack),
        )
