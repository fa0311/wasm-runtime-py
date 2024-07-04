from math import trunc

from src.wasm.runtime.code_exec import CodeSectionBlock
from src.wasm.runtime.debug.check import TypeCheck
from src.wasm.runtime.error.error import (
    WasmIntegerDivideByZeroError,
    WasmIntegerOverflowError,
    WasmInvalidConversionError,
)
from src.wasm.runtime.error.helper import NumpyErrorHelper
from src.wasm.type.numpy.int import I32, I64, SignedI32, SignedI64


class CodeSectionBlockDebug(CodeSectionBlock):
    @NumpyErrorHelper.seterr("raise")
    def i64_div_s(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_div_s()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_div_u(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_div_u()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_s(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_rem_s()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_u(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_rem_u()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_div_s(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_div_s()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_div_u(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_div_u()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_s(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_rem_s()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                self.stack.push(I32.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_u(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_rem_u()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                self.stack.push(I32.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f32_s(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI32)
            return super().i32_trunc_f32_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f32_u(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I32)
            return super().i32_trunc_f32_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f64_s(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI32)
            return super().i32_trunc_f64_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f64_u(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I32)
            return super().i32_trunc_f64_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i64_trunc_f32_s(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI64)
            return super().i64_trunc_f32_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_trunc_f32_u(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I64)
            return super().i64_trunc_f32_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_trunc_f64_s(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI64)
            return super().i64_trunc_f64_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_trunc_f64_u(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I64)
            return super().i64_trunc_f64_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError([I64])
            else:
                raise WasmIntegerOverflowError([I64])
