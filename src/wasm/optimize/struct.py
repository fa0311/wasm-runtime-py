from dataclasses import dataclass

from src.wasm.loader.spec import CodeSectionSpec
from src.wasm.loader.struct import CodeInstruction


@dataclass
class CodeInstructionOptimize(CodeInstruction):
    def __repr__(self):
        cls_name = self.__class__.__name__
        name = CodeSectionSpec.mapped(self.opcode).__name__
        return f"{cls_name}(opcode={self.opcode:02X}, name={name}, args={self.args})"
