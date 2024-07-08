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

    @staticmethod
    def init() -> WasmExec:
        sections = WasmSectionsOptimize(
            type_section=[],
            function_section=[],
            table_section=[],
            memory_section=[],
            global_section=[],
            export_section=[],
            element_section=[],
            code_section=[],
            data_section=[],
        )
        return WasmExecEntry.entry(sections)
