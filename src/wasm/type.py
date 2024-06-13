class NumericType:
    def __init__(self, value):
        self.value = value

    def factory(self, value):
        return NumericType(value)

    def __add__(self, other: "NumericType"):
        return self.factory(self.value + other.value)

    def __sub__(self, other: "NumericType"):
        return self.factory(self.value - other.value)

    def __mul__(self, other: "NumericType"):
        return self.factory(self.value * other.value)

    def __truediv__(self, other: "NumericType"):
        return self.factory(self.value / other.value)

    def __mod__(self, other: "NumericType"):
        return self.factory(self.value % other.value)

    def __eq__(self, other: "NumericType"):
        return self.factory(self.value == other.value)

    def __ne__(self, other: "NumericType"):
        return self.factory(self.value != other.value)

    def __lt__(self, other: "NumericType"):
        return self.factory(self.value < other.value)

    def __le__(self, other: "NumericType"):
        return self.factory(self.value <= other.value)

    def __and__(self, other: "NumericType"):
        return self.factory(self.value & other.value)

    def __or__(self, other: "NumericType"):
        return self.factory(self.value | other.value)

    def __xor__(self, other: "NumericType"):
        return self.factory(self.value ^ other.value)


class LEB128(NumericType):
    def factory(self, value):
        return LEB128(value)


class I32(NumericType):
    def factory(self, value):
        return I32(value)


class I64(NumericType):
    def factory(self, value):
        return I64(value)


class F32(NumericType):
    def factory(self, value):
        return F32(value)


class F64(NumericType):
    def factory(self, value):
        return F64(value)
