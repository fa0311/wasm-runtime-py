from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Union

from src.wasm.optimizer.struct import (
    CodeSectionOptimize,
    MemorySectionOptimize,
    TypeSectionOptimize,
)
from src.wasm.type.base import AnyType
from src.wasm.type.globals.base import GlobalsType
from src.wasm.type.table.base import TableType

if TYPE_CHECKING:
    pass


@dataclass
class WasmExport:
    namespace: str = field(metadata={"description": "Export名前空間"})
    name: str = field(metadata={"description": "Export名"})
    data: Union["WasmExportFunction", "WasmExportTable", "WasmExportMemory", "WasmExportGlobal"]


@dataclass
class WasmExportFunction:
    # function: FunctionSectionOptimize = field(metadata={"description": "Function Sectionのデータ構造"})
    type: TypeSectionOptimize = field(metadata={"description": "Type Sectionのデータ構造"})
    code: "CodeSectionOptimize" = field(metadata={"description": "Code Sectionのデータ構造"})
    call: Callable[[list[AnyType]], list[AnyType]] = field(metadata={"description": "Functionの実行"})


@dataclass
class WasmExportTable:
    table: TableType = field(metadata={"description": "Table Sectionのデータ構造"})


@dataclass
class WasmExportMemory:
    memory: MemorySectionOptimize = field(metadata={"description": "Memory Sectionのデータ構造"})


@dataclass
class WasmExportGlobal:
    globals: GlobalsType = field(metadata={"description": "Global Sectionのデータ構造"})
