from src.wasm.optimizer.struct import WasmSectionsOptimize
from src.wasm.runtime.error.error import (
    WasmCallStackExhaustedError,
)
from src.wasm.runtime.exec import WasmExec
from src.wasm.type.base import NumericType


class WasmExecDebug(WasmExec):
    def __init__(self, sections: WasmSectionsOptimize):
        super().__init__(sections)
        self.instruction_count = 0

    def run_instruction(self):
        self.instruction_count += 1
        if self.instruction_count > 1000000:
            raise Exception("infinite loop")

    def run(self, index: int, param: list[NumericType]):
        try:
            super().run(index, param)
        except RecursionError:
            raise WasmCallStackExhaustedError()
