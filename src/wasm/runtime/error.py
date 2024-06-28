from typing import Callable

import numpy as np

from src.wasm.type.base import NumericType


class WasmError(Exception):
    pass


class WasmInvalidError(WasmError):
    MESSAGE = "invalid"

    def __init__(self):
        self.message = self.MESSAGE


class WasmTypeMismatchError(WasmInvalidError):
    MESSAGE = "type mismatch"


class WasmUnexpectedTokenError(WasmInvalidError):
    MESSAGE = "unexpected token"


class WasmRuntimeError(WasmError):
    MESSAGE = "runtime error"

    def __init__(self, expected: list[type[NumericType]] = []):
        self.expected = expected
        self.message = self.MESSAGE


class WasmIntegerDivideByZeroError(WasmRuntimeError):
    MESSAGE = "integer divide by zero"


class WasmIntegerOverflowError(WasmRuntimeError):
    MESSAGE = "integer overflow"


class WasmCallStackExhaustedError(WasmRuntimeError):
    MESSAGE = "call stack exhausted"


class WasmInvalidConversionError(WasmRuntimeError):
    MESSAGE = "invalid conversion to integer"


class WasmUnimplementedError(WasmError):
    @staticmethod
    def throw():
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                raise WasmUnimplementedError(f"unimplemented: {func.__name__}")

            return wrapper

        return decorator


class NumpyErrorHelper:
    def __init__(self, text):
        self.text = text

    def __enter__(self):
        self.last = np.geterr()
        np.seterr(all=self.text)

    def __exit__(self, exc_type, exc_val, exc_tb):
        np.seterr(**self.last)

    @staticmethod
    def seterr(text):
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                with NumpyErrorHelper(text):
                    return func(*args, **kwargs)

            return wrapper

        return decorator
