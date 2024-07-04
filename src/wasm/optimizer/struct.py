from dataclasses import dataclass, field

from src.tools.byte import ByteReader
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.type.numeric.base import NumericType


@dataclass
class TypeSectionOptimize:
    """Type Sectionのデータ構造"""

    form: int = field(metadata={"description": "関数の形式"})
    params: list[int] = field(metadata={"description": "引数の型"})
    returns: list[int] = field(metadata={"description": "戻り値の型"})


@dataclass
class FunctionSectionOptimize:
    """Function Sectionのデータ構造"""

    type: int = field(metadata={"description": "関数の型"})


@dataclass
class TableSectionOptimize:
    """Table Sectionのデータ構造"""

    element_type: int = field(metadata={"description": "要素の型"})
    limits: int = field(metadata={"description": "要素の制限"})


@dataclass
class MemorySectionOptimize:
    """Memory Sectionのデータ構造"""

    limits: int = field(metadata={"description": "メモリの制限"})


@dataclass
class GlobalSectionOptimize:
    """Global Sectionのデータ構造"""

    type: int = field(metadata={"description": "グローバル変数の型"})
    mutable: int = field(metadata={"description": "グローバル変数の変更可能性"})
    init: bytes = field(metadata={"description": "グローバル変数の初期値"})


@dataclass
class ElementSectionOptimize:
    """Element Sectionのデータ構造"""

    table: int = field(metadata={"description": "テーブルのインデックス"})
    type: bytes = field(metadata={"description": "要素の型"})
    init: list[int] = field(metadata={"description": "初期化"})


@dataclass
class CodeInstructionOptimize:
    """Code Sectionの命令セット"""

    opcode: int = field(metadata={"description": "命令コード"})
    args: list[NumericType] = field(metadata={"description": "命令の引数"})
    child: list["CodeInstructionOptimize"] = field(metadata={"description": "子命令"})
    else_child: list["CodeInstructionOptimize"] = field(metadata={"description": "子命令"})

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        cls_name = self.__class__.__name__
        name = CodeSectionSpecHelper.mapped(self.opcode).__name__
        return f"{cls_name}(opcode={self.opcode:02X}, name={name}, args={self.args})"


@dataclass
class CodeSectionOptimize:
    """Code Sectionのデータ構造"""

    data: list[CodeInstructionOptimize] = field(metadata={"description": "命令セット"})
    local: list[int] = field(metadata={"description": "ローカル変数の型"})


@dataclass
class ExportSectionOptimize:
    """Export Sectionのデータ構造"""

    field_name: ByteReader = field(metadata={"description": "エクスポート名"})
    kind: int = field(metadata={"description": "エクスポートの種類"})
    index: int = field(metadata={"description": "エクスポートのインデックス"})


@dataclass
class WasmSectionsOptimize:
    type_section: list[TypeSectionOptimize]
    function_section: list[FunctionSectionOptimize]
    table_section: list[TableSectionOptimize]
    memory_section: list[MemorySectionOptimize]
    global_section: list[GlobalSectionOptimize]
    element_section: list[ElementSectionOptimize]
    code_section: list[CodeSectionOptimize]
    export_section: list[ExportSectionOptimize]
