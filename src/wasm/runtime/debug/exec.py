from src.wasm.optimizer.struct import WasmSectionsOptimize
from src.wasm.runtime.debug.check import TypeCheck
from src.wasm.runtime.debug.code_exec import CodeSectionBlockDebug
from src.wasm.runtime.error.error import (
    WasmCallStackExhaustedError,
)
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.numeric.base import NumericType


class WasmExecDebug(WasmExec):
    def __init__(self, sections: WasmSectionsOptimize):
        super().__init__(sections)
        self.instruction_count = 0

    def run_instruction(self):
        self.instruction_count += 1
        if self.instruction_count > 1000000:
            raise Exception("infinite loop")

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
