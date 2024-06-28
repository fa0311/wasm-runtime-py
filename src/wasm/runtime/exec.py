import logging
from math import ceil, floor, trunc
from typing import Optional, TypeVar, Union

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
from src.wasm.runtime.error import (
    NumpyErrorHelper,
    WasmIntegerDivideByZeroError,
    WasmIntegerOverflowError,
    WasmInvalidConversionError,
    WasmUnimplementedError,
)
from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64, SignedI8, SignedI16, SignedI32, SignedI64


class WasmExec:
    """Code Sectionのデータ構造"""

    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(self, sections: WasmSectionsOptimize):
        self.sections = sections
        self.stack_cls = NumericStack
        self.code_section_cls = CodeSectionExec

    def type_check(self, param: list[NumericType], params_type: list[int]):
        """型のチェックを行うが、このクラスでは実装しない"""
        pass

    def run_instruction(self):
        """1行呼ばれる前に実行されるが、このクラスでは実装しない"""
        pass

    @logger.logger
    def start(self, field: bytes, param: list[NumericType]):
        """エントリーポイントを実行する"""

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.sections.export_section if fn.field_name == field][0]

        return self.run(start.index, param)

    def run(self, index: int, param: list[NumericType]):
        fn, fn_type = self.get_function(index)

        # ローカル変数とExecインスタンスを生成
        locals_param = [WasmOptimizer.get_type(x).from_int(0) for x in fn.local]
        locals = [*param, *locals_param]
        runner = CodeSectionExec(self, locals=locals, index=index)

        # 型チェックと実行
        self.type_check(param, fn_type.params)
        res = runner.run()
        self.type_check(res, fn_type.returns)

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
            stack=self.env.stack_cls(value=[]),
        )
        res = block.run()
        if isinstance(res, list):
            returns = res
        else:
            returns = [block.stack.any() for _ in self.fn_type.returns][::-1]

        self.logger.debug(f"res: {returns}")
        return returns


class NumericStack:
    value: list[NumericType]
    T = TypeVar("T", bound=NumericType)

    def __init__(self, value: list[NumericType]):
        self.value = value

    def push(self, value: NumericType):
        self.value.append(value)

    def extend(self, value: list[NumericType]):
        self.value.extend(value)

    def any(self, read_only=False) -> NumericType:
        return self.value[-1] if read_only else self.value.pop()

    def __pop(self, value: type[T], read_only=False) -> T:
        item = self.any(read_only)
        if not isinstance(item, value):
            raise Exception("invalid type")
        return item

    def bool(self, read_only=False) -> bool:
        return bool(self.__pop(I32, read_only))

    def i32(self, read_only=False) -> I32:
        return self.__pop(I32, read_only)

    def i64(self, read_only=False) -> I64:
        return self.__pop(I64, read_only)

    def f32(self, read_only=False) -> F32:
        return self.__pop(F32, read_only)

    def f64(self, read_only=False) -> F64:
        return self.__pop(F64, read_only)


class CodeSectionBlock(CodeSectionSpec):
    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(
        self,
        env: WasmExec,
        code: list[CodeInstructionOptimize],
        locals: list[NumericType],
        stack: NumericStack,
    ):
        self.env = env
        self.locals = locals
        self.code = code

        self.stack = stack
        self.pointer = 0
        self.instruction: CodeInstructionOptimize

    @logger.logger
    def run(self) -> Optional[Union[int, list[NumericType]]]:
        self.logger.debug(f"params: {self.stack.value}")
        while self.pointer < len(self.code):
            self.env.run_instruction()
            self.instruction = self.code[self.pointer]
            opcode = self.instruction.opcode
            args = self.instruction.args
            self.logger.debug(f"run: {self.instruction}")
            fn = CodeSectionSpecHelper.bind(self, opcode)
            self.pointer += 1
            res = fn(*args)
            if res is not None:
                return res

    def type_check(self, value: NumericType, clamp: type[NumericType], raise_cls: type[NumericType]):
        """型チェックを行う"""
        min_value = value.__class__.from_int(clamp.get_min())
        max_value = value.__class__.from_int(clamp.get_max())

        # if np.isnan(value.value):
        #     return cls.from_int(0)
        # if np.isinf(value.value):
        #     if np.signbit(value.value):
        #         return cls.from_int(clamp.get_min())
        #     else:
        #         return cls.from_int(clamp.get_max())

        if value.value < min_value.value:
            raise WasmIntegerOverflowError([raise_cls])

        if value.value > max_value.value:
            raise WasmIntegerOverflowError([raise_cls])

    # Control Instructions

    def unreachable(self):
        raise Exception("unreachable")

    def nop(self):
        pass

    def block(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.any() for _ in fn_type_params][::-1]
        self.env.type_check(block_stack, fn_type_params)

        block = CodeSectionBlock(
            env=self.env,
            code=self.instruction.child,
            locals=self.locals,
            stack=NumericStack(value=[]),
        )
        br = block.run()

        res_stack = [block.stack.any() for _ in fn_type_returns][::-1]
        self.env.type_check(res_stack, fn_type_returns)
        self.stack.extend(res_stack)

        if isinstance(br, int) and br > 0:
            return br - 1
        elif isinstance(br, list):
            return br

    def loop(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.any() for _ in fn_type_params][::-1]
        self.env.type_check(block_stack, fn_type_params)
        while True:
            block = CodeSectionBlock(
                env=self.env,
                code=self.instruction.child,
                locals=self.locals,
                stack=NumericStack(value=block_stack),
            )
            br = block.run()

            if br == 0:
                block_stack = [block.stack.any() for _ in fn_type_params][::-1]
                self.env.type_check(block_stack, fn_type_params)
            else:
                res_stack = [block.stack.any() for _ in fn_type_returns][::-1]
                self.env.type_check(res_stack, fn_type_returns)
                self.stack.extend(res_stack)
                if isinstance(br, int) and br > 0:
                    return br - 1
                elif isinstance(br, list):
                    return br
                else:
                    break

    def if_(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.any() for _ in fn_type_params][::-1]
        self.env.type_check(block_stack, fn_type_params)

        code = self.instruction.child if bool(self.stack.any()) else self.instruction.else_child
        block = CodeSectionBlock(
            env=self.env,
            code=code,
            locals=self.locals,
            stack=NumericStack(value=block_stack),
        )
        br = block.run()

        res_stack = [block.stack.any() for _ in fn_type_returns][::-1]
        self.env.type_check(res_stack, fn_type_returns)
        self.stack.extend(res_stack)

        if isinstance(br, int) and br > 0:
            return br - 1
        elif isinstance(br, list):
            return br

    def else_(self):
        Exception("else_")

    def block_end(self):
        Exception("block_end")

    def br(self, count: int):
        return count

    def br_if(self, count: int):
        if self.stack.bool():
            return count
        else:
            pass

    def br_table(self, count: list[int]):
        a = self.stack.i32()
        return count[a.value]

    def return_(self):
        a = self.stack.any()
        return [a]

    def call(self, index: int):
        _, fn_type = self.env.get_function(index)

        param = [self.stack.any() for _ in fn_type.params][::-1]

        runtime, res = self.env.run(index, param)

        self.stack.extend(res)

    @WasmUnimplementedError.throw()
    def call_indirect(self, index: int):
        pass

    def drop(self):
        self.stack.any()

    def select(self):
        c, b, a = self.stack.i32(), self.stack.any(), self.stack.any()
        self.stack.push(a if c else b)

    # Variable Instructions

    def local_get(self, index: int):
        self.stack.push(self.locals[index])

    def local_set(self, index: int):
        self.locals[index] = self.stack.any()

    def local_tee(self, index: int):
        self.locals[index] = self.stack.any(read_only=True)

    def i32_const(self, value: I32):
        self.stack.push(value)

    def i64_const(self, value: I64):
        self.stack.push(value)

    def f32_const(self, value: F32):
        self.stack.push(value)

    def f64_const(self, value: F64):
        self.stack.push(value)

    def i32_eqz(self):
        a = self.stack.i32()
        self.stack.push(a == I32.from_int(0))

    def i32_eq(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a == b)

    def i32_ne(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a != b)

    def i32_lt_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(sa < sb)

    def i32_lt_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a < b)

    def i32_gt_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(sa > sb)

    def i32_gt_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a > b)

    def i32_le_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(sa <= sb)

    def i32_le_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a <= b)

    def i32_ge_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(sa >= sb)

    def i32_ge_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a >= b)

    def i64_eqz(self):
        a = self.stack.i64()
        self.stack.push(a == I64.from_int(0))

    def i64_eq(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a == b)

    def i64_ne(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a != b)

    def i64_lt_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(sa < sb)

    def i64_lt_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a < b)

    def i64_gt_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(sa > sb)

    def i64_gt_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a > b)

    def i64_le_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(sa <= sb)

    def i64_le_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a <= b)

    def i64_ge_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(sa >= sb)

    def i64_ge_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a >= b)

    def f32_eq(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a == b)

    def f32_ne(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a != b)

    def f32_lt(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a < b)

    def f32_gt(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a > b)

    def f32_le(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a <= b)

    def f32_ge(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a >= b)

    def f64_eq(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a == b)

    def f64_ne(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a != b)

    def f64_lt(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a < b)

    def f64_gt(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a > b)

    def f64_le(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a <= b)

    def f64_ge(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a >= b)

    def i32_clz(self):
        a = self.stack.i32()
        self.stack.push(a.clz())

    def i32_ctz(self):
        a = self.stack.i32()
        self.stack.push(a.ctz())

    def i32_popcnt(self):
        a = self.stack.i32()
        self.stack.push(a.popcnt())

    def i32_add(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a + b)

    def i32_sub(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a - b)

    def i32_mul(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a * b)

    @NumpyErrorHelper.seterr("raise")
    def i32_div_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        try:
            self.stack.push(I32.astype(sa / sb))
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_div_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        try:
            self.stack.push(a / b)
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        try:
            self.stack.push(I32.astype(sa % sb))
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                self.stack.push(I32.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i32_rem_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        try:
            self.stack.push(a % b)
        except FloatingPointError:
            if b == I32.from_int(0):
                raise WasmIntegerDivideByZeroError([I32])
            else:
                self.stack.push(I32.from_int(0))

    def i32_and(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a & b)

    def i32_or(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a | b)

    def i32_xor(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a ^ b)

    def i32_shl(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a << b)

    def i32_shr_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(I32.astype(sa >> sb))

    def i32_shr_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a >> b)

    def i32_rotl(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a.rotl(b))

    def i32_rotr(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a.rotr(b))

    def i64_clz(self):
        a = self.stack.i64()
        self.stack.push(a.clz())

    def i64_ctz(self):
        a = self.stack.i64()
        self.stack.push(a.ctz())

    def i64_popcnt(self):
        a = self.stack.i64()
        self.stack.push(a.popcnt())

    def i64_add(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a + b)

    def i64_sub(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a - b)

    def i64_mul(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a * b)

    @NumpyErrorHelper.seterr("raise")
    def i64_div_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        try:
            self.stack.push(I64.astype(sa / sb))
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_div_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        try:
            self.stack.push(a / b)
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                raise WasmIntegerOverflowError([I64])

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        try:
            self.stack.push(I64.astype(sa % sb))
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                self.stack.push(I64.from_int(0))

    @NumpyErrorHelper.seterr("raise")
    def i64_rem_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        try:
            self.stack.push(a % b)
        except FloatingPointError:
            if b == I64.from_int(0):
                raise WasmIntegerDivideByZeroError([I64])
            else:
                self.stack.push(I64.from_int(0))

    def i64_and(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a & b)

    def i64_or(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a | b)

    def i64_xor(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a ^ b)

    def i64_shl(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a << b)

    def i64_shr_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(I64.astype(sa >> sb))

    def i64_shr_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a >> b)

    def i64_rotl(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a.rotl(b))

    def i64_rotr(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a.rotr(b))

    def f32_abs(self):
        a = self.stack.f32()
        self.stack.push(abs(a))

    def f32_neg(self):
        a = self.stack.f32()
        self.stack.push(-a)

    def f32_ceil(self):
        a = self.stack.f32()
        self.stack.push(ceil(a))

    def f32_floor(self):
        a = self.stack.f32()
        self.stack.push(floor(a))

    def f32_trunc(self):
        a = self.stack.f32()
        self.stack.push(trunc(a))

    def f32_nearest(self):
        a = self.stack.f32()
        self.stack.push(round(a))

    def f32_sqrt(self):
        a = self.stack.f32()
        self.stack.push(a.sqrt())

    def f32_add(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a + b)

    def f32_sub(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a - b)

    def f32_mul(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a * b)

    def f32_div(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a / b)

    def f32_min(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a.min(b))

    def f32_max(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a.max(b))

    def f32_copysign(self):
        b, a = self.stack.f32(), self.stack.f32()
        self.stack.push(a.copysign(b))

    def f64_abs(self):
        a = self.stack.f64()
        self.stack.push(abs(a))

    def f64_neg(self):
        a = self.stack.f64()
        self.stack.push(-a)

    def f64_ceil(self):
        a = self.stack.f64()
        self.stack.push(ceil(a))

    def f64_floor(self):
        a = self.stack.f64()
        self.stack.push(floor(a))

    def f64_trunc(self):
        a = self.stack.f64()
        self.stack.push(trunc(a))

    def f64_nearest(self):
        a = self.stack.f64()
        self.stack.push(round(a))

    def f64_sqrt(self):
        a = self.stack.f64()
        self.stack.push(a.sqrt())

    def f64_add(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a + b)

    def f64_sub(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a - b)

    def f64_mul(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a * b)

    def f64_div(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a / b)

    def f64_min(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a.min(b))

    def f64_max(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a.max(b))

    def f64_copysign(self):
        b, a = self.stack.f64(), self.stack.f64()
        self.stack.push(a.copysign(b))

    def i32_wrap_i64(self):
        a = self.stack.i64()
        self.stack.push(I32.astype(a))

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f32_s(self):
        a = self.stack.f32()
        try:
            t = trunc(a)
            self.type_check(t, SignedI32, I32)
            i32 = SignedI32.astype(t)
            self.stack.push(I32.astype(i32))
        except FloatingPointError:
            if a.is_nan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f32_u(self):
        a = self.stack.f32()
        try:
            t = trunc(a)
            self.type_check(t, I32, I32)
            i32 = I32.astype(t)
            self.stack.push(i32)
        except FloatingPointError:
            if a.is_nan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f64_s(self):
        a = self.stack.f64()
        try:
            t = trunc(a)
            self.type_check(t, SignedI32, I32)
            i32 = SignedI32.astype(t)
            self.stack.push(I32.astype(i32))
        except FloatingPointError:
            if a.is_nan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    @NumpyErrorHelper.seterr("raise")
    def i32_trunc_f64_u(self):
        a = self.stack.f64()
        try:
            t = trunc(a)
            self.type_check(t, I32, I32)
            i32 = I32.astype(t)
            self.stack.push(i32)
        except FloatingPointError:
            if a.is_nan():
                raise WasmInvalidConversionError([I32])
            else:
                raise WasmIntegerOverflowError([I32])

    def i64_extend_i32_s(self):
        a = self.stack.i32()
        sa = SignedI32.astype(a)
        self.stack.push(I64.astype(sa))

    def i64_extend_i32_u(self):
        a = self.stack.i32()
        self.stack.push(I64.astype(a))

    def f32_convert_i32_s(self):
        a = self.stack.i32()
        sa = SignedI32.astype(a)
        self.stack.push(F32.astype(sa))

    def f32_convert_i32_u(self):
        a = self.stack.i32()
        self.stack.push(F32.astype(a))

    def f32_convert_i64_s(self):
        a = self.stack.i64()
        sa = SignedI64.astype(a)
        self.stack.push(F32.astype(sa))

    def f32_convert_i64_u(self):
        a = self.stack.i64()
        self.stack.push(F32.astype(a))

    def f32_demote_f64(self):
        a = self.stack.f64()
        self.stack.push(F32.astype(a))

    def f64_convert_i32_s(self):
        a = self.stack.i32()
        sa = SignedI32.astype(a)
        self.stack.push(F64.astype(sa))

    def f64_convert_i32_u(self):
        a = self.stack.i32()
        self.stack.push(F64.astype(a))

    def f64_convert_i64_s(self):
        a = self.stack.i64()
        sa = SignedI64.astype(a)
        self.stack.push(F64.astype(sa))

    def f64_convert_i64_u(self):
        a = self.stack.i64()
        self.stack.push(F64.astype(a))

    def f64_promote_f32(self):
        a = self.stack.f32()
        self.stack.push(F64.astype(a))

    def i32_reinterpret_f32(self):
        a = self.stack.f32()
        bit = a.to_bits()
        self.stack.push(I32.from_bits(bit))

    def i64_reinterpret_f64(self):
        a = self.stack.f64()
        bit = a.to_bits()
        self.stack.push(I64.from_bits(bit))

    def f32_reinterpret_i32(self):
        a = self.stack.i32()
        bit = a.to_bits()
        self.stack.push(F32.from_bits(bit))

    def f64_reinterpret_i64(self):
        a = self.stack.i64()
        bit = a.to_bits()
        self.stack.push(F64.from_bits(bit))

    def i32_extend8_s(self):
        a = self.stack.i32()
        sa = SignedI8.astype(a)
        self.stack.push(I32.astype(sa))

    def i32_extend16_s(self):
        a = self.stack.i32()
        sa = SignedI16.astype(a)
        self.stack.push(I32.astype(sa))

    def i64_extend8_s(self):
        a = self.stack.i64()
        sa = SignedI8.astype(a)
        self.stack.push(I64.astype(sa))

    def i64_extend16_s(self):
        a = self.stack.i64()
        sa = SignedI16.astype(a)
        self.stack.push(I64.astype(sa))

    def i64_extend32_s(self):
        a = self.stack.i64()
        sa = SignedI32.astype(a)
        self.stack.push(I64.astype(sa))

    def i64_trunc_f32_s(self):
        a = self.stack.f32()
        i64 = I64.from_value_with_clamp(trunc(a), SignedI64)
        self.stack.push(i64)

    def i64_trunc_f32_u(self):
        a = self.stack.f32()
        i64 = I64.from_value_with_clamp(trunc(a), I64)
        self.stack.push(i64)

    def i64_trunc_f64_s(self):
        a = self.stack.f64()
        i64 = I64.from_value_with_clamp(trunc(a), SignedI64)
        self.stack.push(I64.astype(i64))

    def i64_trunc_f64_u(self):
        a = self.stack.f64()
        i64 = I64.from_value_with_clamp(trunc(a), I64)
        self.stack.push(i64)

    def i32_trunc_sat_f32_s(self):
        a = self.stack.f32()
        i32 = I32.from_value_with_clamp(trunc(a), SignedI32)
        self.stack.push(i32)

    def i32_trunc_sat_f32_u(self):
        a = self.stack.f32()
        i32 = I32.from_value_with_clamp(trunc(a), I32)
        self.stack.push(i32)

    def i32_trunc_sat_f64_s(self):
        a = self.stack.f64()
        i32 = I32.from_value_with_clamp(trunc(a), SignedI32)
        self.stack.push(I32.astype(i32))

    def i32_trunc_sat_f64(self):
        a = self.stack.f64()
        i32 = I32.from_value_with_clamp(trunc(a), I32)
        self.stack.push(i32)

    def i64_trunc_sat_f32_s(self):
        a = self.stack.f32()
        i64 = I64.from_value_with_clamp(trunc(a), SignedI64)
        self.stack.push(i64)

    def i64_trunc_sat_f32(self):
        a = self.stack.f32()
        i64 = I64.from_value_with_clamp(trunc(a), I64)
        self.stack.push(i64)

    def i64_trunc_sat_f64_s(self):
        a = self.stack.f64()
        i64 = I64.from_value_with_clamp(trunc(a), SignedI64)
        self.stack.push(I64.astype(i64))

    def i64_trunc_sat_f64(self):
        a = self.stack.f64()
        i64 = I64.from_value_with_clamp(trunc(a), I64)
        self.stack.push(i64)

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
