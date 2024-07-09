import os

from src.wasm.optimizer.struct import WasmSectionsOptimize
from src.wasm.runtime.check.exec import WasmExecCheck, WasmExecRelease
from src.wasm.runtime.exec import WasmExec


class WasmExecEntry:
    @staticmethod
    def entry(sections: WasmSectionsOptimize) -> WasmExec:
        if os.getenv("WASM_FAST") == "true":
            return WasmExecRelease(sections)
        else:
            return WasmExecCheck(sections)

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
