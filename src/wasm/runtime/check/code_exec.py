from math import trunc

from src.wasm.runtime.check.check import TypeCheck
from src.wasm.runtime.code_exec import CodeSectionBlock
from src.wasm.runtime.error.error import (
    WasmIndirectCallTypeMismatchError,
    WasmIntegerDivideByZeroError,
    WasmIntegerOverflowError,
    WasmInvalidConversionError,
    WasmOutOfBoundsMemoryAccessError,
    WasmUndefinedElementError,
    WasmUnreachableError,
)
from src.wasm.runtime.error.helper import NumpyErrorHelper
from src.wasm.type.numeric.numpy.int import I32, I64, SignedI32, SignedI64


class CodeSectionBlockDebug(CodeSectionBlock):
    def unreachable(self):
        raise WasmUnreachableError()

    def call_indirect(self, index: int, elm_index: int):
        fn_type_params, fn_type_returns = self.env.get_type(index)
        a = self.stack.i32(read_only=True)
        element = self.env.sections.element_section[elm_index]

        try:
            __, fn_type = self.env.get_function(element.funcidx[a.value])
            TypeCheck.list_check(fn_type.params, fn_type_params)
            TypeCheck.list_check(fn_type.returns, fn_type_returns or [])
            return super().call_indirect(index, elm_index)
        except IndexError:
            raise WasmUndefinedElementError()
        except TypeError:
            raise WasmIndirectCallTypeMismatchError()

    def i32_store(self, align: int, offset: int):
        try:
            return super().i32_store(align, offset)
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()

    def i64_store(self, align: int, offset: int):
        try:
            return super().i64_store(align, offset)
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_div_s(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_div_s()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i64_div_u(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_div_u()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_s(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_rem_s()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_u(self):
        b = self.stack.i64(read_only=True, key=-2)
        try:
            return super().i64_rem_u()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_div_s(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_div_s()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i32_div_u(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_div_u()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_s(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_rem_s()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I32.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_u(self):
        b = self.stack.i32(read_only=True, key=-2)
        try:
            return super().i32_rem_u()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I32.from_int(0))

    def i32_trunc_f32_s(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI32)
            return super().i32_trunc_f32_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i32_trunc_f32_u(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I32)
            return super().i32_trunc_f32_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i32_trunc_f64_s(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI32)
            return super().i32_trunc_f64_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i32_trunc_f64_u(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I32)
            return super().i32_trunc_f64_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i64_trunc_f32_s(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI64)
            return super().i64_trunc_f32_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i64_trunc_f32_u(self):
        a = self.stack.f32(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I64)
            return super().i64_trunc_f32_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i64_trunc_f64_s(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), SignedI64)
            return super().i64_trunc_f64_s()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()

    def i64_trunc_f64_u(self):
        a = self.stack.f64(read_only=True)
        try:
            TypeCheck.cast_check(trunc(a), I64)
            return super().i64_trunc_f64_u()
        except FloatingPointError:
            if a.isnan():
                raise WasmInvalidConversionError()
            else:
                raise WasmIntegerOverflowError()
