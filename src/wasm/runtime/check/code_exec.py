from math import trunc

from src.wasm.runtime.check.check import TypeCheck
from src.wasm.runtime.code_exec import CodeSectionBlock
from src.wasm.runtime.error.error import (
    WasmIndirectCallTypeMismatchError,
    WasmIntegerDivideByZeroError,
    WasmIntegerOverflowError,
    WasmInvalidConversionError,
    WasmOutOfBoundsMemoryAccessError,
    WasmOutOfBoundsTableAccessError,
    WasmUndefinedElementError,
    WasmUninitialized2ElementError,
    WasmUninitializedElementError,
    WasmUnreachableError,
)
from src.wasm.runtime.error.helper import NumpyErrorHelper
from src.wasm.type.numeric.numpy.int import I16, I32, I64, SignedI32, SignedI64


class CodeSectionBlockDebug(CodeSectionBlock):
    def unreachable(self):
        raise WasmUnreachableError()

    def call_indirect(self, index: int, elm_index: int):
        fn_type_params, fn_type_returns = self.env.get_type(index)
        a = self.stack.i32(read_only=True)

        element = self.env.tables[elm_index]

        try:
            table = self.env.tables[elm_index]
            if all(x.is_none() for x in table):
                raise WasmUninitialized2ElementError()
            if table[int(a)].is_none():
                raise WasmUninitializedElementError()
            b, fn_type = self.env.get_function(int(element[int(a)]))
            TypeCheck.list_check(fn_type.params, fn_type_params)
            TypeCheck.list_check(fn_type.returns, fn_type_returns or [])
            return super().call_indirect(index, elm_index)
        except IndexError:
            raise WasmUndefinedElementError()
        except TypeError:
            raise WasmIndirectCallTypeMismatchError()

    def table_get(self, index: int):
        try:
            return super().table_get(index)
        except IndexError:
            raise WasmOutOfBoundsTableAccessError()

    def table_set(self, index: int):
        try:
            return super().table_set(index)
        except IndexError:
            raise WasmOutOfBoundsTableAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_load(self, align: int, offset: int):
        try:
            return super().i32_load(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load(self, align: int, offset: int):
        try:
            return super().i64_load(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def f32_load(self, align: int, offset: int):
        try:
            return super().f32_load(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def f64_load(self, align: int, offset: int):
        try:
            return super().f64_load(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_load8_s(self, align: int, offset: int):
        try:
            return super().i32_load8_s(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_load8_u(self, align: int, offset: int):
        try:
            return super().i32_load8_u(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_load16_s(self, align: int, offset: int):
        try:
            return super().i32_load16_s(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_load16_u(self, align: int, offset: int):
        try:
            return super().i32_load16_u(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load8_s(self, align: int, offset: int):
        try:
            return super().i64_load8_s(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load8_u(self, align: int, offset: int):
        try:
            return super().i64_load8_u(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load16_s(self, align: int, offset: int):
        try:
            return super().i64_load16_s(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load16_u(self, align: int, offset: int):
        try:
            return super().i64_load16_u(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load32_s(self, align: int, offset: int):
        try:
            return super().i64_load32_s(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_load32_u(self, align: int, offset: int):
        try:
            return super().i64_load32_u(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_store(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(4):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i32_store(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_store(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(8):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i64_store(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def f32_store(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(4):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().f32_store(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def f64_store(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(8):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().f64_store(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_store8(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(1):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i32_store8(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i32_store16(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(2):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i32_store16(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_store8(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(1):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i64_store8(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_store16(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(2):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i64_store16(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def i64_store32(self, align: int, offset: int):
        addr = self.stack.i32(read_only=True, key=-2)
        try:
            if I32.from_int(len(self.env.memory)) < addr + I32.from_int(4):
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().i64_store32(align, offset)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    def memory_grow(self, index: int):
        a = self.stack.i32(read_only=True)
        b = len(self.env.memory) // 64 // 1024
        section = self.env.sections.memory_section[index]

        if I32.from_int(section.limits_max or I16.get_max()) < a + I32.from_int(b):
            self.stack.i32()
            self.stack.push(I32.astype(SignedI32.from_int(-1)))
        else:
            return super().memory_grow(index)

    @NumpyErrorHelper.seterr("raise")
    def i64_div_s(self):
        b = self.stack.i64(read_only=True)
        try:
            return super().i64_div_s()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i64_div_u(self):
        b = self.stack.i64(read_only=True)
        try:
            return super().i64_div_u()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_s(self):
        b = self.stack.i64(read_only=True)
        try:
            return super().i64_rem_s()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_u(self):
        b = self.stack.i64(read_only=True)
        try:
            return super().i64_rem_u()
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_div_s(self):
        b = self.stack.i32(read_only=True)
        try:
            return super().i32_div_s()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i32_div_u(self):
        b = self.stack.i32(read_only=True)
        try:
            return super().i32_div_u()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                raise WasmIntegerOverflowError()

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_s(self):
        b = self.stack.i32(read_only=True)
        try:
            return super().i32_rem_s()
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError()
            else:
                self.stack.push(I32.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_u(self):
        b = self.stack.i32(read_only=True)
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

    @NumpyErrorHelper.seterr("raise")
    def memory_init(self, index: int, index2: int):
        c, b, a = (
            self.stack.i32(read_only=True, key=-1),
            self.stack.i32(read_only=True, key=-2),
            self.stack.i32(read_only=True, key=-3),
        )
        memory = self.env.init_memory[index]
        try:
            if I32.from_int(len(self.env.memory)) < a + c:
                raise WasmOutOfBoundsMemoryAccessError()
            elif I32.from_int(len(memory)) < b + c:
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().memory_init(index, index2)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def memory_copy(self, index: int, index2: int):
        c, b, a = (
            self.stack.i32(read_only=True, key=-1),
            self.stack.i32(read_only=True, key=-2),
            self.stack.i32(read_only=True, key=-3),
        )
        try:
            if I32.from_int(len(self.env.memory)) < a + c:
                raise WasmOutOfBoundsMemoryAccessError()
            elif I32.from_int(len(self.env.memory)) < b + c:
                raise WasmOutOfBoundsMemoryAccessError()
            elif I32.from_int(len(self.env.memory)) < a + c:
                raise WasmOutOfBoundsMemoryAccessError()
            elif I32.from_int(len(self.env.memory)) < b + c:
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().memory_copy(index, index2)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    @NumpyErrorHelper.seterr("raise")
    def memory_fill(self, index: int):
        c, a = self.stack.i32(read_only=True, key=-1), self.stack.i32(read_only=True, key=-3)
        try:
            if I32.from_int(len(self.env.memory)) < a + c:
                raise WasmOutOfBoundsMemoryAccessError()
            else:
                return super().memory_fill(index)
        except IndexError:
            raise WasmOutOfBoundsMemoryAccessError()
        except ValueError:
            raise WasmOutOfBoundsMemoryAccessError()
        except FloatingPointError:
            raise WasmOutOfBoundsMemoryAccessError()

    def table_init(self, index: int, index2: int):
        c, b, a = (
            self.stack.i32(read_only=True, key=-1),
            self.stack.i32(read_only=True, key=-2),
            self.stack.i32(read_only=True, key=-3),
        )
        if len(self.env.tables) <= index2:
            raise WasmOutOfBoundsTableAccessError()
        if len(self.env.sections.element_section) <= index2:
            raise WasmOutOfBoundsTableAccessError()
        if int(a) + int(c) > len(self.env.tables[index2]):
            raise WasmOutOfBoundsTableAccessError()
        if int(b) + int(c) > len(self.env.sections.element_section[index2].get_funcidx()):
            raise WasmOutOfBoundsTableAccessError()
        return super().table_init(index, index2)

    def table_copy(self, index: int, index2: int):
        c, b, a = (
            self.stack.int(read_only=True, key=-1),
            self.stack.int(read_only=True, key=-2),
            self.stack.int(read_only=True, key=-3),
        )
        try:
            if a + c > len(self.env.tables[index]):
                raise WasmOutOfBoundsTableAccessError()
            if b + c > len(self.env.tables[index2]):
                raise WasmOutOfBoundsTableAccessError()
            return super().table_copy(index, index2)
        except IndexError:
            raise WasmOutOfBoundsTableAccessError()

    @NumpyErrorHelper.seterr("raise")
    def table_grow(self, index: int):
        a = self.stack.i32(read_only=True)
        table_type, table = self.env.get_table(index)
        try:
            if I32.from_int(table_type.limits_max or I32.get_max()) < I32.from_int(len(table)) + a:
                self.stack.push(I32.astype(SignedI32.from_int(-1)))
            else:
                return super().table_grow(index)
        except FloatingPointError:
            self.stack.push(I32.astype(SignedI32.from_int(-1)))

    def table_fill(self, index: int):
        c, a = self.stack.i32(read_only=True, key=-1), self.stack.i32(read_only=True, key=-3)
        if a.value + c.value > len(self.env.tables[index]):
            raise WasmOutOfBoundsTableAccessError()
        return super().table_fill(index)
