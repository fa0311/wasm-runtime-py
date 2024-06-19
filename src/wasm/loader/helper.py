from typing import Callable, List, Optional

from src.wasm.loader.spec import CodeSectionSpec
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
            if hasattr(v, "metadata"):
                for m in v.metadata:
                    data[m] = v

        return data.get(opcode, cls.naver)

    @classmethod
    def bind(cls, pearent: "CodeSectionSpec", opcode: int) -> BindingType:
        name = cls.mapped(opcode)
        if name is cls.naver:
            raise Exception(f"opcode: {opcode:02X} is not defined")
        return getattr(pearent, name.__name__)
