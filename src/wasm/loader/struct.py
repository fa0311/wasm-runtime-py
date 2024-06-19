from dataclasses import dataclass, field

from tools.byte import ByteReader

from src.wasm.type.base import NumericType


class SectionBase:
    """Sectionのデータ構造"""


@dataclass
class TypeSection(SectionBase):
    """Type Sectionのデータ構造"""

    form: int = field(metadata={"description": "関数の形式"})
    params: list[int] = field(metadata={"description": "引数の型"})
    returns: list[int] = field(metadata={"description": "戻り値の型"})


@dataclass
class FunctionSection(SectionBase):
    """Function Sectionのデータ構造"""

    type: int = field(metadata={"description": "関数の型"})


@dataclass
class CodeInstruction:
    """Code Sectionの命令セット"""

    opcode: int = field(metadata={"description": "命令コード"})
    args: list[NumericType] = field(metadata={"description": "命令の引数"})


@dataclass
class CodeSection(SectionBase):
    """Code Sectionのデータ構造"""

    data: list[CodeInstruction] = field(metadata={"description": "命令セット"})
    local: list[int] = field(metadata={"description": "ローカル変数の型"})


@dataclass
class ExportSection(SectionBase):
    """Export Sectionのデータ構造"""

    field: ByteReader
    kind: int
    index: int
