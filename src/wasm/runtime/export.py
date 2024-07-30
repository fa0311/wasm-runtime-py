from dataclasses import dataclass, field
from typing import Callable, Union

from src.wasm.optimizer.struct import (
    FunctionSectionOptimize,
    GlobalSectionOptimize,
    MemorySectionOptimize,
    TableSectionOptimize,
)
from src.wasm.type.base import AnyType


@dataclass
class WasmExport:
    namespace: str = field(metadata={"description": "Export名前空間"})
    name: str = field(metadata={"description": "Export名"})
    data: Union["WasmExportFunction", "WasmExportTable", "WasmExportMemory", "WasmExportGlobal"]


@dataclass
class WasmExportFunction:
    function: FunctionSectionOptimize = field(metadata={"description": "Function Sectionのデータ構造"})
    # code: "CodeSectionOptimize" = field(metadata={"description": "Code Sectionのデータ構造"})
    call: Callable[[list[AnyType]], list[AnyType]] = field(metadata={"description": "Functionの実行"})


@dataclass
class WasmExportTable:
    table: TableSectionOptimize = field(metadata={"description": "Table Sectionのデータ構造"})


@dataclass
class WasmExportMemory:
    memory: MemorySectionOptimize = field(metadata={"description": "Memory Sectionのデータ構造"})


@dataclass
class WasmExportGlobal:
    global_: GlobalSectionOptimize = field(metadata={"description": "Global Sectionのデータ構造"})
