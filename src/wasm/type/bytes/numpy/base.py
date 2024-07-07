import numpy as np

from src.wasm.type.bytes.base import BytesType


class NumpyBytesType(BytesType):
    def __init__(self, value: np.ndarray):
        self.value = value

    @classmethod
    def from_size(cls, size: int):
        return cls(np.zeros(size, dtype=np.uint8))

    def store(self, offset: int, value: bytes):
        data = np.frombuffer(value, dtype=np.uint8)
        self.value[offset : offset + len(data)] = data

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value

    def __len__(self):
        return len(self.value)

    def grow(self, size: int):
        self.value = np.concatenate([self.value, np.zeros(size, dtype=np.uint8)])
