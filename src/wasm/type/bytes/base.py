class BytesType:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_size(cls, size: int):
        return cls([0] * size)

    def __getitem__(self, key):
        return self.value[key]

    def __setitem__(self, key, value):
        self.value[key] = value
