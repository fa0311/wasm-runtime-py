from typing import Any, Callable, Optional

from src.wasm.loader.spec import BlockType, CodeSectionSpec
from src.wasm.type.base import NumericType

BindingType = Callable[[NumericType], Optional[Any]]


class CodeSectionSpecHelper:
    def never(self):
        raise Exception("never calle")

    @classmethod
    def mapped(cls, opcode: int) -> Callable:
        value = CodeSectionSpec.__dict__.values()
        data = {}
        for v in value:
            if hasattr(v, "opcode"):
                for m in v.opcode:
                    data[m] = v
        return data.get(opcode, cls.never)

    @classmethod
    def is_prefix(cls, opcode: int) -> bool:
        """2バイトのopcodeの先頭かどうかを判定する"""
        value = CodeSectionSpec.__dict__.values()
        prefix = {}
        for v in value:
            if hasattr(v, "opcode"):
                for m in v.opcode:
                    if m > 0xFF:
                        prefix[m >> 8] = True
        return opcode in prefix

    @classmethod
    def bind(cls, pearent: "CodeSectionSpec", opcode: int) -> BindingType:
        fn = cls.mapped(opcode)
        if fn is cls.never:
            raise Exception(f"opcode: {opcode:02X} is not defined")
        return getattr(pearent, fn.__name__)

    @classmethod
    def get_block_type(cls, opcode: int) -> Optional[BlockType]:
        name = cls.mapped(opcode)
        return getattr(name, "block", None)
