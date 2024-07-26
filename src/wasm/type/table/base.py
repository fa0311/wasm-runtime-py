from typing import Optional

from src.wasm.type.ref.base import RefType


class TableType:
    def __init__(self, type: type[RefType], min: int, max: Optional[int] = None):
        self.type = type
        self.min = min
        self.max = max
        self.init = False
        self.value = [type.from_null() for _ in range(min)]

    def __getitem__(self, key) -> RefType:
        return self.value.__getitem__(key)

    def __setitem__(self, key, value):
        self.value.__setitem__(key, value)

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def pop(self, key: int = -1):
        return self.value.pop(key)
