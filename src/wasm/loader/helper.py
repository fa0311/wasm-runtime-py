from typing import Callable, List, Optional

from src.wasm.loader.spec import BlockType, CodeSectionSpec
from src.wasm.type.base import NumericType

BindingType = Callable[[NumericType], Optional[List[NumericType]]]


class CodeSectionSpecHelper:
    def naver(self):
        raise Exception("naver calle")

    @classmethod
    def mapped(cls, opcode: int) -> Callable:
        value = CodeSectionSpec.__dict__.values()
        data = {}
        for v in value:
            if hasattr(v, "opcode"):
                for m in v.opcode:
                    data[m] = v
        return data.get(opcode, cls.naver)

    @classmethod
    def bind(cls, pearent: "CodeSectionSpec", opcode: int) -> BindingType:
        fn = cls.mapped(opcode)
        if fn is cls.naver:
            raise Exception(f"opcode: {opcode:02X} is not defined")
        return getattr(pearent, fn.__name__)

    @classmethod
    def get_block_type(cls, opcode: int) -> Optional[BlockType]:
        name = cls.mapped(opcode)
        return getattr(name, "block", None)
