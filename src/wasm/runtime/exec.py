import logging
from math import ceil, floor, trunc
from typing import Callable, Optional, Union

from src.tools.logger import NestedLogger
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import CodeSectionSpec
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
    CodeSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)
from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64, SignedI8, SignedI16, SignedI32, SignedI64


class WasmUnimplementedError(NotImplementedError):
    @staticmethod
    def throw():
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                raise WasmUnimplementedError(f"unimplemented: {func.__name__}")

            return wrapper

        return decorator


class WasmExec:
    """Code Sectionのデータ構造"""

    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(self, sections: WasmSectionsOptimize):
        self.sections = sections
        self.instruction_count = 0

    @staticmethod
    def __type_check(param: list[NumericType], params_type: list[int]):
        if len(param) != len(params_type):
            raise Exception("invalid param length")
        for a, b in zip(param, params_type):
            if a.__class__ != WasmOptimizer.get_type(b):
                raise Exception(f"invalid return type {a.__class__} != {WasmOptimizer.get_type(b)}")

    @staticmethod
    def __type_check_release(param: list[NumericType], params_type: list[int]):
        return None

    if __debug__:
        type_check = __type_check
    else:
        type_check = __type_check_release

    @logger.logger
    def start(self, field: bytes, param: list[NumericType]):
        """エントリーポイントを実行する"""

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.sections.export_section if fn.field_name == field][0]

        return self.run(start.index, param)

    def run(self, index: int, param: list[NumericType]):
        fn, fn_type = self.get_function(index)

        locals_param = [WasmOptimizer.get_type(x).from_int(0) for x in fn.local]
        locals = [*param, *locals_param]
        runner = CodeSectionExec(self, locals=locals, index=index)

        WasmExec.type_check(param, fn_type.params)
        res = runner.run()
        WasmExec.type_check(res, fn_type.returns)

        return (runner, res)

    def get_function(self, index: int) -> tuple[CodeSectionOptimize, TypeSectionOptimize]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        fn = self.sections.function_section[index]
        type = self.sections.type_section[fn.type]
        code = self.sections.code_section[index]
        return code, type

    def get_type(self, index: int) -> tuple[list[int], list[int]]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        if index < len(self.sections.type_section):
            type = self.sections.type_section[index]
            return type.params, type.returns
        else:
            type = WasmOptimizer.get_type_or_none(index)
            returns = [] if type is None else [type]
            return [], returns


class CodeSectionExec:
    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(self, env: WasmExec, locals: list[NumericType], index: int):
        self.env = env
        self.locals = locals
        self.code, self.fn_type = self.env.get_function(index)
        self.pointer = 0

    def run(self):
        block = CodeSectionBlock(
            env=self.env,
            code=self.code.data,
            locals=self.locals,
            stack=[],
        )
        res = block.run()
        if isinstance(res, list):
            returns = res
        else:
            returns = [block.stack.pop() for _ in self.fn_type.returns][::-1]

        self.logger.debug(f"res: {returns}")
        return returns


class CodeSectionBlock(CodeSectionSpec):
    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(
        self,
        env: WasmExec,
        code: list[CodeInstructionOptimize],
        locals: list[NumericType],
        stack: list[NumericType],
    ):
        self.env = env
        self.locals = locals
        self.code = code
        # self.code, self.fn_type = self.env.get_function(index)

        self.stack = stack
        self.pointer = 0
        self.instruction: CodeInstructionOptimize

    @logger.logger
    def run(self) -> Optional[Union[int, list[NumericType]]]:
        self.logger.debug(f"params: {self.stack}")
        while self.pointer < len(self.code):
            if __debug__:
                self.env.instruction_count += 1
                if self.env.instruction_count > 1000000:
                    raise Exception("infinite loop")

            self.instruction = self.code[self.pointer]
            opcode = self.instruction.opcode
            args = self.instruction.args
            self.logger.debug(f"run: {self.instruction}")
            fn = CodeSectionSpecHelper.bind(self, opcode)
            self.pointer += 1
            res = fn(*args)
            if res is not None:
                return res

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

    def if_(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.pop() for _ in fn_type_params][::-1]
        WasmExec.type_check(block_stack, fn_type_params)

        code = self.instruction.child if bool(self.stack.pop()) else self.instruction.else_child
        block = CodeSectionBlock(
            env=self.env,
            code=code,
            locals=self.locals,
            stack=block_stack,
        )
        br = block.run()

        res_stack = [block.stack.pop() for _ in fn_type_returns][::-1]
        WasmExec.type_check(res_stack, fn_type_returns)
        self.stack.extend(res_stack)

        if isinstance(br, int) and br > 0:
            return br - 1
        elif isinstance(br, list):
            return br

    def else_(self):
        Exception("else_")

    def br_if(self, count: int):
        a = self.stack.pop()
        if bool(a):
            return count
        else:
            pass

    def br_table(self, count: list[int]):
        a = self.stack.pop()
        return count[a.value]

    def br(self, count: int):
        return count

    def unreachable(self):
        raise Exception("unreachable")

    def nop(self):
        pass

    def block(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.pop() for _ in fn_type_params][::-1]
        WasmExec.type_check(block_stack, fn_type_params)

        block = CodeSectionBlock(
            env=self.env,
            code=self.instruction.child,
            locals=self.locals,
            stack=block_stack,
        )
        br = block.run()

        res_stack = [block.stack.pop() for _ in fn_type_returns][::-1]
        WasmExec.type_check(res_stack, fn_type_returns)
        self.stack.extend(res_stack)

        if isinstance(br, int) and br > 0:
            return br - 1
        elif isinstance(br, list):
            return br

    def loop(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.pop() for _ in fn_type_params][::-1]
        WasmExec.type_check(block_stack, fn_type_params)
        while True:
            block = CodeSectionBlock(
                env=self.env,
                code=self.instruction.child,
                locals=self.locals,
                stack=block_stack,
            )
            br = block.run()

            if br == 0:
                block_stack = [block.stack.pop() for _ in fn_type_params][::-1]
                WasmExec.type_check(block_stack, fn_type_params)
            else:
                res_stack = [block.stack.pop() for _ in fn_type_returns][::-1]
                WasmExec.type_check(res_stack, fn_type_returns)
                self.stack.extend(res_stack)
                if isinstance(br, int) and br > 0:
                    return br - 1
                elif isinstance(br, list):
                    return br
                else:
                    break

    def block_end(self):
        Exception("block_end")

    def call(self, index: int):
        _, fn_type = self.env.get_function(index)

        param = [self.stack.pop() for _ in fn_type.params][::-1]

        runtime, res = self.env.run(index, param)

        self.stack.extend(res)

    @WasmUnimplementedError.throw()
    def call_indirect(self, index: int):
        pass

    def drop(self):
        self.stack.pop()

    def select(self):
        c, b, a = self.stack.pop(), self.stack.pop(), self.stack.pop()
        self.stack.append(a if c else b)

    def return_(self):
        a = self.stack.pop()
        return [a]

    def wrap_i64(self):
        a = self.stack.pop()
        i32 = I32.from_value(a.value)
        self.stack.append(i32)

    def i32_trunc_f32_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        self.stack.append(i32.to_unsigned())

    def i32_trunc_f32(self):
        a = self.stack.pop()
        i32 = I32.from_value(a.value)
        self.stack.append(i32)

    def i32_trunc_f64_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        self.stack.append(i32.to_unsigned())

    def i32_trunc_f64(self):
        a = self.stack.pop()
        i32 = I32.from_value(a.value)
        self.stack.append(i32)

    def i64_extend_i32(self):
        a = self.stack.pop()
        i64 = I64.from_value(a.value)
        self.stack.append(i64)

    def i64_extend_i32_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        i64 = I64.from_value(i32.value)
        self.stack.append(i64)

    def f32_convert_i32_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        f32 = F32.from_value(i32.value)
        self.stack.append(f32)

    def f32_convert_i32(self):
        a = self.stack.pop()
        f32 = F32.from_value(a.value)
        self.stack.append(f32)

    def f32_convert_i64_s(self):
        a = self.stack.pop()
        i64 = SignedI64.from_value(a.value)
        f32 = F32.from_value(i64.value)
        self.stack.append(f32)

    def f32_convert_i64(self):
        a = self.stack.pop()
        f32 = F32.from_value(a.value)
        self.stack.append(f32)

    def f32_demote_f64(self):
        a = self.stack.pop()
        f32 = F32.from_value(a.value)
        self.stack.append(f32)

    def f64_convert_i32_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(a.value)
        f64 = F64.from_value(i32.value)
        self.stack.append(f64)

    def f64_convert_i32(self):
        a = self.stack.pop()
        f64 = F64.from_value(a.value)
        self.stack.append(f64)

    def f64_convert_i64_s(self):
        a = self.stack.pop()
        i64 = SignedI64.from_value(a.value)
        f64 = F64.from_value(i64.value)
        self.stack.append(f64)

    def f64_convert_i64(self):
        a = self.stack.pop()
        f64 = F64.from_value(a.value)
        self.stack.append(f64)

    def f64_promote_f32(self):
        a = self.stack.pop()
        f64 = F64.from_value(a.value)
        self.stack.append(f64)

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

    @WasmUnimplementedError.throw()
    def i64_trunc_f32_s(self):
        a = self.stack.pop()
        i64 = SignedI64.from_value(a.value)
        self.stack.append(i64.to_unsigned())

    @WasmUnimplementedError.throw()
    def i64_trunc_f32(self):
        a = self.stack.pop()
        i64 = I64.from_value(a.value)
        self.stack.append(i64)

    @WasmUnimplementedError.throw()
    def i64_trunc_f64_s(self):
        a = self.stack.pop()
        i64 = SignedI64.from_value(a.value)
        self.stack.append(i64.to_unsigned())

    @WasmUnimplementedError.throw()
    def i64_trunc_f64(self):
        a = self.stack.pop()
        i64 = I64.from_value(a.value)
        self.stack.append(i64)

    @WasmUnimplementedError.throw()
    def i32_trunc_sat_f32_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(trunc(a).value)
        self.stack.append(i32.to_unsigned())

    @WasmUnimplementedError.throw()
    def i32_trunc_sat_f32(self):
        a = self.stack.pop()
        i32 = I32.from_value(a.value)
        self.stack.append(i32)

    @WasmUnimplementedError.throw()
    def i32_trunc_sat_f64_s(self):
        a = self.stack.pop()
        i32 = SignedI32.from_value(trunc(a).value)
        self.stack.append(i32.to_unsigned())

    @WasmUnimplementedError.throw()
    def i32_trunc_sat_f64(self):
        a = self.stack.pop()
        i32 = I32.from_value(trunc(a).value)
        self.stack.append(i32)

    @WasmUnimplementedError.throw()
    def i64_trunc_sat_f32_s(self):
        a = self.stack.pop()
        i64 = SignedI64.from_value(trunc(a).value)
        self.stack.append(i64.to_unsigned())

    @WasmUnimplementedError.throw()
    def i64_trunc_sat_f32(self):
        a = self.stack.pop()
        i64 = I64.from_value(trunc(a).value)
        self.stack.append(i64)

    @WasmUnimplementedError.throw()
    def i64_trunc_sat_f64_s(self):
        a = self.stack.pop()
        i64 = SignedI64.from_value(trunc(a).value)
        self.stack.append(i64.to_unsigned())

    @WasmUnimplementedError.throw()
    def i64_trunc_sat_f64(self):
        a = self.stack.pop()
        i64 = I64.from_value(trunc(a).value)
        self.stack.append(i64)

    def memory_init(self):
        pass

    def data_drop(self):
        pass

    def memory_copy(self):
        pass

    def memory_fill(self):
        pass

    def table_init(self):
        pass

    def elem_drop(self):
        pass

    def table_copy(self):
        pass

    def table_grow(self):
        pass

    def table_size(self):
        pass

    def table_fill(self):
        pass
