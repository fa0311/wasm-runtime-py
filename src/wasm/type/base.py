class AnyType:
    def __init__(self, value):
        self.value = value

    def __int__(self):
        return self.value.__int__()

    def is_none(self):
        return self.value is None

    @classmethod
    def from_null(cls):
        return cls(None)
