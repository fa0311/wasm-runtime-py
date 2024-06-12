from dataclasses import dataclass

from tools.byte import ByteReader


@dataclass
class TypeSection:
    """Type Sectionのデータ構造"""

    form: int
    params: list[int]
    returns: list[int]


@dataclass
class FunctionSection:
    """Function Sectionのデータ構造"""

    type: int


@dataclass
class CodeSection:
    """Code Sectionのデータ構造"""

    data: ByteReader
    local: list[int]


@dataclass
class ExportSection:
    """Export Sectionのデータ構造"""

    field: ByteReader
    kind: int
    index: int
