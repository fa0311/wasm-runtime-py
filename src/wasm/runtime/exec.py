import logging
from math import ceil, floor, trunc

from src.tools.logger import NestedLogger
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import CodeSectionSpec
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
    CodeSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)
from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64, SignedI8, SignedI16, SignedI32


class WasmExec:
    """Code Sectionのデータ構造"""

    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(self, sections: WasmSectionsOptimize):
        self.sections = sections
        self.instruction_count = 0

    def get_number_type(self, type: int) -> type[NumericType]:
        if type == 0x7F:
            return I32
        if type == 0x7E:
            return I64
        if type == 0x7D:
            return F32
        if type == 0x7C:
            return F64
        raise Exception(f"invalid type: {type}")

    @logger.logger
    def start(self, field: bytes, param: list[NumericType]):
        """エントリーポイントを実行する"""

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.sections.export_section if fn.field_name == field][0]
        fn, fn_type = self.get_function(start.index)

        # ローカル変数を初期化して実行する
        param = [self.get_number_type(x).from_value(param.pop(0).value) for x in fn_type.params]
        locals_param = [self.get_number_type(x).from_int(0) for x in fn.local]
        locals = [*param, *locals_param]
        runner = CodeSectionExec(self, code=fn.data, locals=locals)

        # res = runner.run()
        # returns = [self.get_number_type(x).from_int(res.pop(0)) for x in fn_type.returns]

        # デバッグ用の変数を初期化
        self.instruction_count = 0

        return runner

    def get_function(self, index: int) -> tuple[CodeSectionOptimize, TypeSectionOptimize]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        fn = self.sections.function_section[index]
        type = self.sections.type_section[fn.type]
        code = self.sections.code_section[index]
        return code, type


class CodeSectionExec(CodeSectionSpec):
    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(
        self,
        env: WasmExec,
        code: list[CodeInstructionOptimize],
        locals: list[NumericType],
    ):
        self.env = env
        self.code = code
        self.locals = locals

        self.stack: list[NumericType] = []
        self.pointer = 0

    @logger.logger
    def run(self) -> list[NumericType]:
        while self.pointer < len(self.code):
            if __debug__:
                self.env.instruction_count += 1
                if self.env.instruction_count > 10000:
                    raise Exception("infinite loop")

            instruction = self.code[self.pointer]
            opcode = instruction.opcode
            args = instruction.args
            self.logger.debug(f"run: {instruction}")
            fn = CodeSectionSpecHelper.bind(self, opcode)
            res = fn(*args)
            if res:
                return res

            self.pointer += 1
        return self.stack

    def goto_start(self, index: int):
        self.pointer = self.code[self.pointer].block_start[-(index + 1)]
        self.logger.debug(f"goto: {self.pointer}")

    def goto_end(self, index: int):
        self.pointer = self.code[self.pointer].block_end[-(index + 1)]
        self.logger.debug(f"goto: {self.pointer}")

    def goto_start_or_end(self, index: int):
        if self.code[self.pointer].loop:
            self.goto_start(index)
        else:
            self.goto_end(index)

    def const_i32(self, value: I32):
        self.stack.append(value)

    def const_i64(self, value: I64):
        self.stack.append(value)

    def const_f32(self, value: F32):
        self.stack.append(value)

    def const_f64(self, value: F64):
        self.stack.append(value)

    def local_get(self, index: int):
        self.stack.append(self.locals[index])

    def local_set(self, index: int):
        self.locals[index] = self.stack.pop()

    def local_tee(self, index: int):
        self.locals[index] = self.stack[-1]

    def add(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a + b)

    def sub(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a - b)

    def mul(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a * b)

    def div(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a / b)

    def div_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append((sa / sb).to_unsigned())

    def rem(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a % b)

    def rem_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append((sa % sb).to_unsigned())

    def eq(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a == b)

    def ne(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a != b)

    def eqz(self):
        a = self.stack.pop()
        self.stack.append(a == I32.from_int(0))

    def gt_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append(sa > sb)

    def gt_u(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a > b)

    def ge(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a >= b)

    def ge_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append(sa >= sb)

    def lt_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append(sa < sb)

    def lt_u(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a < b)

    def le(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a <= b)

    def le_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append(sa <= sb)

    def clz(self):
        a = self.stack.pop()
        self.stack.append(a.clz())

    def ctz(self):
        a = self.stack.pop()
        self.stack.append(a.ctz())

    def popcnt(self):
        a = self.stack.pop()
        self.stack.append(a.popcnt())

    def and_(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a & b)

    def or_(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a | b)

    def xor(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a ^ b)

    def shl(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a << b)

    def shr_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append((sa >> sb).to_unsigned())

    def shr_u(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a >> b)

    def rotl(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a.rotl(b))

    def rotr(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a.rotr(b))

    def abs(self):
        a = self.stack.pop()
        self.stack.append(abs(a))

    def neg(self):
        a = self.stack.pop()
        self.stack.append(-a)

    def ceil(self):
        a = self.stack.pop()
        self.stack.append(ceil(a))

    def floor(self):
        a = self.stack.pop()
        self.stack.append(floor(a))

    def trunc(self):
        a = self.stack.pop()
        self.stack.append(trunc(a))

    def nearest(self):
        a = self.stack.pop()
        self.stack.append(round(a))

    def min(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a.min(b))

    def max(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a.max(b))

    def sqrt(self):
        a = self.stack.pop()
        self.stack.append(a.sqrt())

    def copysign(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a.copysign(b))

    def if_(self, type: int):
        a = self.stack.pop()
        if not bool(a):
            self.goto_end(0)

    def else_(self):
        self.goto_end(0)

    def br_if(self, count: int):
        a = self.stack.pop()
        if bool(a):
            self.goto_start_or_end(count)

    def br(self, count: int):
        self.goto_start_or_end(count)

    def block(self, block_type: int):
        pass

    def loop(self, block_type: int):
        pass

    def block_end(self):
        pass

    def call(self, index: int):
        fn, fn_type = self.env.get_function(index)
        param = [self.env.get_number_type(x).from_value(self.stack.pop().value) for x in fn_type.params]
        locals_param = [self.env.get_number_type(x).from_int(0) for x in fn.local]
        locals = [*param, *locals_param]
        runner = CodeSectionExec(self.env, code=fn.data, locals=locals)
        res = runner.run()
        returns = [self.env.get_number_type(x).from_value(res.pop(0).value) for x in fn_type.returns]
        self.stack.extend(returns)

    def drop(self):
        self.stack.pop()

    def return_(self):
        return [self.stack.pop()]

    def wrap_i64(self):
        a = self.stack.pop()
        i64 = I64.from_value(a.value)
        self.stack.append(i64)

    def i64_extend_i32(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        i64 = I64.from_value(i32.value)
        self.stack.append(i64)

    def i64_extend_i32_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        i64 = I64.from_value(i32.value)
        self.stack.append(i64)

    def i32_extend8(self):
        a = self.stack.pop()
        i8 = SignedI8.from_value(a.value)
        i32 = I32.from_value(i8.value)
        self.stack.append(i32)

    def i32_extend16(self):
        a = self.stack.pop()
        i16 = SignedI16.from_value(a.value)
        i32 = I32.from_value(i16.value)
        self.stack.append(i32)

    def i64_extend8(self):
        a = self.stack.pop()
        i8 = SignedI8.from_value(a.value)
        i64 = I64.from_value(i8.value)
        self.stack.append(i64)

    def i64_extend16(self):
        a = self.stack.pop()
        i16 = SignedI16.from_value(a.value)
        i64 = I64.from_value(i16.value)
        self.stack.append(i64)

    def i64_extend32(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        i64 = I64.from_value(i32.value)
        self.stack.append(i64)
