from dataclasses import dataclass, field

from src.tools.byte import ByteReader
from src.wasm.type.base import NumericType


@dataclass
class TypeSection:
    """Type Sectionのデータ構造"""

    form: int = field(metadata={"description": "関数の形式"})
    params: list[int] = field(metadata={"description": "引数の型"})
    returns: list[int] = field(metadata={"description": "戻り値の型"})


@dataclass
class FunctionSection:
    """Function Sectionのデータ構造"""

    type: int = field(metadata={"description": "関数の型"})


@dataclass
class TableSection:
    """Table Sectionのデータ構造"""

    element_type: int = field(metadata={"description": "要素の型"})
    limits: int = field(metadata={"description": "要素の制限"})


@dataclass
class MemorySection:
    """Memory Sectionのデータ構造"""

    limits: int = field(metadata={"description": "メモリの制限"})


@dataclass
class GlobalSection:
    """Global Sectionのデータ構造"""

    type: int = field(metadata={"description": "グローバル変数の型"})
    mutable: int = field(metadata={"description": "グローバル変数の変更可能性"})
    init: bytes = field(metadata={"description": "グローバル変数の初期値"})


@dataclass
class ElementSection:
    """Element Sectionのデータ構造"""

    table: int = field(metadata={"description": "テーブルのインデックス"})
    type: bytes = field(metadata={"description": "要素の型"})
    init: list[int] = field(metadata={"description": "初期化"})


@dataclass
class CodeInstruction:
    """Code Sectionの命令セット"""

    opcode: int = field(metadata={"description": "命令コード"})
    args: list[NumericType] = field(metadata={"description": "命令の引数"})

    if __debug__:

        def __repr__(self):
            from src.wasm.loader.helper import CodeSectionSpecHelper

            cls_name = self.__class__.__name__
            name = CodeSectionSpecHelper.mapped(self.opcode).__name__
            return f"{cls_name}(opcode={self.opcode:02X}, name={name}, args={self.args})"


@dataclass
class CodeSection:
    """Code Sectionのデータ構造"""

    data: list[CodeInstruction] = field(metadata={"description": "命令セット"})
    local: list[int] = field(metadata={"description": "ローカル変数の型"})


@dataclass
class ExportSection:
    """Export Sectionのデータ構造"""

    field_name: ByteReader = field(metadata={"description": "エクスポート名"})
    kind: int = field(metadata={"description": "エクスポートの種類"})
    index: int = field(metadata={"description": "エクスポートのインデックス"})


@dataclass
class WasmSections:
    type_section: list[TypeSection]
    function_section: list[FunctionSection]
    table_section: list[TableSection]
    memory_section: list[MemorySection]
    global_section: list[GlobalSection]
    element_section: list[ElementSection]
    code_section: list[CodeSection]
    export_section: list[ExportSection]
