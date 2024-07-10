from src.wasm.type.ref.base import RefType


class TableType:
    def __init__(self, value: list):
        self.value = value

    @classmethod
    def from_size(cls, type: type[RefType], size: int):
        return cls([type.from_null() for _ in range(size)])

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __len__(self):
        return len(self.value)

    def pop(self, key: int = -1):
        return self.value.pop(key)
