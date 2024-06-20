from dataclasses import dataclass, field
from typing import Optional

from src.tools.byte import ByteReader
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.type.base import NumericType


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
class CodeInstructionOptimize:
    """Code Sectionの命令セット"""

    opcode: int = field(metadata={"description": "命令コード"})
    args: list[NumericType] = field(metadata={"description": "命令の引数"})
    loop: Optional[int] = field(metadata={"description": "親の命令コード"})
    block_start: list[int] = field(metadata={"description": "ブロックの開始位置"})
    block_end: list[int] = field(metadata={"description": "ブロックの終了位置"})

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
    code_section: list[CodeSectionOptimize]
    export_section: list[ExportSectionOptimize]
