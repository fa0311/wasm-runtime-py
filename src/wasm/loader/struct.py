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
class CodeInstruction:
    """Code Sectionの命令セット"""

    opcode: int = field(metadata={"description": "命令コード"})
    args: list[NumericType] = field(metadata={"description": "命令の引数"})


@dataclass
class CodeSection:
    """Code Sectionのデータ構造"""

    data: list[CodeInstruction] = field(metadata={"description": "命令セット"})
    local: list[int] = field(metadata={"description": "ローカル変数の型"})


@dataclass
class ExportSection:
    """Export Sectionのデータ構造"""

    field: ByteReader
    kind: int
    index: int


@dataclass
class WasmSections:
    type_section: list[TypeSection]
    function_section: list[FunctionSection]
    code_section: list[CodeSection]
    export_section: list[ExportSection]
