from typing import Callable


class WasmError(Exception):
    MESSAGE = "error"
    OTHER_MESSAGE = []

    def __init__(self):
        self.message = self.MESSAGE
        self.other_message = self.OTHER_MESSAGE


class WasmInvalidError(WasmError):
    MESSAGE = "invalid"


class WasmTypeMismatchError(WasmInvalidError):
    MESSAGE = "type mismatch"


class WasmUnexpectedTokenError(WasmInvalidError):
    MESSAGE = "unexpected token"


class WasmRuntimeError(WasmError):
    MESSAGE = "runtime error"


class WasmIntegerDivideByZeroError(WasmRuntimeError):
    MESSAGE = "integer divide by zero"


class WasmIntegerOverflowError(WasmRuntimeError):
    MESSAGE = "integer overflow"


class WasmCallStackExhaustedError(WasmRuntimeError):
    MESSAGE = "call stack exhausted"


class WasmInvalidConversionError(WasmRuntimeError):
    MESSAGE = "invalid conversion to integer"


class WasmUndefinedElementError(WasmRuntimeError):
    MESSAGE = "undefined element"


class WasmUninitializedElementError(WasmRuntimeError):
    MESSAGE = "uninitialized element"
    OTHER_MESSAGE = ["uninitialized element 2"]


class WasmIndirectCallTypeMismatchError(WasmRuntimeError):
    MESSAGE = "indirect call type mismatch"


class WasmOutOfBoundsMemoryAccessError(WasmRuntimeError):
    MESSAGE = "out of bounds memory access"


class WasmUnreachableError(WasmRuntimeError):
    MESSAGE = "unreachable"


class WasmOutOfBoundsTableAccessError(WasmRuntimeError):
    MESSAGE = "out of bounds table access"


class WasmUnimplementedError(WasmError):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    @staticmethod
    def throw():
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                raise WasmUnimplementedError(f"unimplemented: {func.__name__}")

            return wrapper

        return decorator
