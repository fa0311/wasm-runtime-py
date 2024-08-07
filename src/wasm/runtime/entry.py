import os

from src.wasm.optimizer.struct import WasmSectionsOptimize
from src.wasm.runtime.check.exec import WasmExecCheck, WasmExecRelease
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.export import WasmExport


class WasmExecEntry:
    @staticmethod
    def entry(sections: WasmSectionsOptimize, export: list[WasmExport] = []) -> WasmExec:
        if os.getenv("WASM_FAST") == "true":
            return WasmExecRelease(sections, export)
        else:
            return WasmExecCheck(sections, export)

    @staticmethod
    def init() -> WasmExec:
        sections = WasmSectionsOptimize(
            import_section=[],
            type_section=[],
            function_section=[],
            table_section=[],
            memory_section=[],
            start_section=[],
            global_section=[],
            export_section=[],
            element_section=[],
            code_section=[],
            data_section=[],
        )
        return WasmExecEntry.entry(sections)
