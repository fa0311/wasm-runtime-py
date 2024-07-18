from typing import Optional

from src.wasm.type.ref.base import RefType


class TableType:
    def __init__(self, type: type[RefType], min: int, max: Optional[int] = None):
        self.type = type
        self.min = min
        self.max = max
        self.value = [None for _ in range(min)]

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __len__(self):
        return len(self.value)

    def pop(self, key: int = -1):
        return self.value.pop(key)
