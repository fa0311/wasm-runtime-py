from src.wasm.optimizer.struct import WasmSectionsOptimize
from src.wasm.runtime.debug.exec import WasmExecDebug
from src.wasm.runtime.exec import WasmExec


class WasmExecEntry:
    @staticmethod
    def entry(sections: WasmSectionsOptimize) -> WasmExec:
        if __debug__:
            return WasmExecDebug(sections)
        else:
            return WasmExec(sections)
