class AnyType:
    def __init__(self, value):
        self.value = value

    @classmethod
    def from_null(cls):
        return cls(None)
