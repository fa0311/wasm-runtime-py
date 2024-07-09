from src.wasm.type.base import AnyType


class RefType(AnyType):
    @classmethod
    def from_value(cls, value):
        return cls(value)


class ExternRef(RefType):
    pass


class FuncRef(RefType):
    pass
