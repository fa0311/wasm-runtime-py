from dataclasses import dataclass
from typing import Optional

from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.struct import CodeInstruction


@dataclass
class CodeInstructionOptimize(CodeInstruction):
    goto: Optional[int] = None

    def __repr__(self):
        cls_name = self.__class__.__name__
        name = CodeSectionSpecHelper.mapped(self.opcode).__name__
        return f"{cls_name}(opcode={self.opcode:02X}, name={name}, args={self.args})"
