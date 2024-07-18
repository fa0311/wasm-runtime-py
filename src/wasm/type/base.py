class AnyType:
    def __init__(self, value):
        self.value = value

    def __int__(self):
        return self.value.__int__()

    @classmethod
    def from_null(cls):
        return cls(None)
