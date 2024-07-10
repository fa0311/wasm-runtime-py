from typing import Any, Callable, Optional, Union

from src.wasm.loader.spec import BlockType, CodeSectionSpec
from src.wasm.type.numeric.base import NumericType

ArgumentType = Union[NumericType, int, list[int]]
BindingType = Callable[[ArgumentType], Optional[Any]]


class CodeSectionSpecHelperUtil:
    @classmethod
    def get_opcode(cls) -> dict[int, Callable]:
        value = CodeSectionSpec.__dict__.values()
        data = {}
        for v in value:
            if hasattr(v, "opcode"):
                for m in v.opcode:
                    data[m] = v
        return data

    @classmethod
    def get_multi_byte_opcode(cls) -> dict[int, Callable]:
        value = CodeSectionSpec.__dict__.values()
        data = {}
        for v in value:
            if hasattr(v, "opcode"):
                for m in v.opcode:
                    if m > 0xFF:
                        data[m >> 8] = v
        return data


class CodeSectionSpecHelper:
    opcode = CodeSectionSpecHelperUtil.get_opcode()
    multi_byte_opcode = CodeSectionSpecHelperUtil.get_multi_byte_opcode()

    def never(self):
        raise Exception("never calle")

    @classmethod
    def mapped(cls, opcode: int) -> Callable:
        return cls.opcode.get(opcode, cls.never)

    @classmethod
    def is_prefix(cls, opcode: int) -> bool:
        """2バイトのopcodeの先頭かどうかを判定する"""
        return opcode in cls.multi_byte_opcode

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
