from dataclasses import dataclass, field
from typing import Union

from src.wasm.optimizer.struct import (
    CodeSectionOptimize,
    FunctionSectionOptimize,
    GlobalSectionOptimize,
    MemorySectionOptimize,
    TableSectionOptimize,
)


@dataclass
class WasmExport:
    namespace: str = field(metadata={"description": "Export名前空間"})
    name: str = field(metadata={"description": "Export名"})
    data: Union["WasmExportFunction", "WasmExportTable", "WasmExportMemory", "WasmExportGlobal"]


@dataclass
class WasmExportFunction:
    function: FunctionSectionOptimize = field(metadata={"description": "Function Sectionのデータ構造"})
    code: "CodeSectionOptimize" = field(metadata={"description": "Code Sectionのデータ構造"})


@dataclass
class WasmExportTable:
    table: TableSectionOptimize = field(metadata={"description": "Table Sectionのデータ構造"})


@dataclass
class WasmExportMemory:
    memory: MemorySectionOptimize = field(metadata={"description": "Memory Sectionのデータ構造"})


@dataclass
class WasmExportGlobal:
    global_: GlobalSectionOptimize = field(metadata={"description": "Global Sectionのデータ構造"})
