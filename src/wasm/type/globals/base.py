from src.wasm.type.base import AnyType


class GlobalsType:
    def __init__(self, value: AnyType):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value
