from typing import TypeVar

from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64


class NumericStack:
    value: list[NumericType]
    T = TypeVar("T", bound=NumericType)

    def __init__(self, value: list[NumericType]):
        self.value = value

    def push(self, value: NumericType):
        self.value.append(value)

    def extend(self, value: list[NumericType]):
        self.value.extend(value)

    def any(self, read_only=False, key=-1) -> NumericType:
        return self.value[key] if read_only else self.value.pop()

    def __len__(self):
        return len(self.value)

    def __pop(self, value: type[T], read_only=False, key=-1) -> T:
        item = self.any(read_only)
        if not isinstance(item, value):
            raise Exception("invalid type")
        return item

    def bool(self, read_only=False, key=-1) -> bool:
        return bool(self.__pop(I32, read_only, key))

    def i32(self, read_only=False, key=-1) -> I32:
        return self.__pop(I32, read_only, key)

    def i64(self, read_only=False, key=-1) -> I64:
        return self.__pop(I64, read_only, key)

    def f32(self, read_only=False, key=-1) -> F32:
        return self.__pop(F32, read_only, key)

    def f64(self, read_only=False, key=-1) -> F64:
        return self.__pop(F64, read_only, key)
