from math import ceil, floor, trunc

from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.check.check import TypeCheck
from src.wasm.runtime.run import CodeSectionRun
from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I8, I16, I32, I64, SignedI8, SignedI16, SignedI32, SignedI64
from src.wasm.type.ref.base import FuncRef


class CodeSectionBlock(CodeSectionRun):
    def unreachable(self):
        pass

    def nop(self):
        pass

    def block(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.any() for _ in fn_type_params][::-1]
        TypeCheck.type_check(block_stack, fn_type_params)

        block = self.env.get_block(locals=self.locals, stack=block_stack)
        br = block.run(self.instruction.child)

        if isinstance(br, list):
            return br

        if fn_type_returns is None:
            res_stack = block.stack.all()
        else:
            res_stack = [block.stack.any() for _ in fn_type_returns][::-1]
            TypeCheck.type_check(res_stack, fn_type_returns)

        self.stack.extend(res_stack)

        if isinstance(br, int) and br > 0:
            return br - 1

    def loop(self, block_type: int):
        fn_type_params, fn_type_returns = self.env.get_type(block_type)
        block_stack = [self.stack.any() for _ in fn_type_params][::-1]
        TypeCheck.type_check(block_stack, fn_type_params)
        while True:
            block = self.env.get_block(locals=self.locals, stack=block_stack)
            br = block.run(self.instruction.child)
            if isinstance(br, list):
                return br
            elif br == 0:
                block_stack = [block.stack.any() for _ in fn_type_params][::-1]
                TypeCheck.type_check(block_stack, fn_type_params)
            else:
                if fn_type_returns is None or len(fn_type_returns) == 0:
                    res_stack = block.stack.all()
                else:
                    res_stack = [block.stack.any() for _ in fn_type_returns][::-1]
                    TypeCheck.type_check(res_stack, fn_type_returns)
                self.stack.extend(res_stack)
                if isinstance(br, int) and br > 0:
                    return br - 1
                else:
                    break

    def if_(self, block_type: int):
        a = self.stack.bool()
        code = self.instruction.child if a else self.instruction.else_child
        if len(code) > 0:
            fn_type_params, fn_type_returns = self.env.get_type(block_type)
            block_stack = [self.stack.any() for _ in fn_type_params][::-1]
            TypeCheck.type_check(block_stack, fn_type_params)
            block = self.env.get_block(locals=self.locals, stack=block_stack)
            br = block.run(code)

            if isinstance(br, list):
                return br

            if fn_type_returns is None:
                res_stack = block.stack.all()
            else:
                res_stack = [block.stack.any() for _ in fn_type_returns][::-1]
                TypeCheck.type_check(res_stack, fn_type_returns)
            self.stack.extend(res_stack)

            if isinstance(br, int) and br > 0:
                return br - 1

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
        a = self.stack.int()
        return count[a] if a < len(count) else count[-1]

    def return_(self):
        return self.stack.all()

    def call(self, index: int):
        _, fn_type = self.env.get_function(index)
        param = [self.stack.any() for _ in fn_type.params][::-1]
        res = self.env.functions[index](param)
        self.stack.extend(res)

    def call_indirect(self, index: int, elm_index: int):
        a = self.stack.int()
        table = self.env.tables[elm_index]
        self.call(int(table[a]))

    def drop(self):
        self.stack.any()

    def select(self):
        c, b, a = self.stack.bool(), self.stack.any(), self.stack.any()
        self.stack.push(a if c else b)

    def select_t(self, _: int, type: int):
        c, b, a = self.stack.bool(), self.stack.any(), self.stack.any()
        self.stack.push(a if c else b)

    # Variable Instructions

    def local_get(self, index: int):
        self.stack.push(self.locals[index])

    def local_set(self, index: int):
        self.locals[index] = self.stack.any()

    def local_tee(self, index: int):
        self.locals[index] = self.stack.any(read_only=True)

    def global_get(self, index: int):
        self.stack.push(self.env.globals[index])

    def global_set(self, index: int):
        self.env.globals[index] = self.stack.any()

    def table_get(self, index: int):
        a = self.stack.int()
        self.stack.push(self.env.tables[index][a])

    def table_set(self, index: int):
        b, a = self.stack.ref(), self.stack.int()
        self.env.tables[index][a] = b

    def i32_load(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        self.stack.push(I32.from_bits(self.env.memory[addr : addr + 4]))

    def i64_load(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        self.stack.push(I64.from_bits(self.env.memory[addr : addr + 8]))

    def f32_load(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        self.stack.push(F32.from_bits(self.env.memory[addr : addr + 4]))

    def f64_load(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        self.stack.push(F64.from_bits(self.env.memory[addr : addr + 8]))

    def i32_load8_s(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i8 = SignedI8.from_bits(self.env.memory[addr : addr + 1])
        self.stack.push(I32.astype(i8))

    def i32_load8_u(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i8 = I8.from_bits(self.env.memory[addr : addr + 1])
        self.stack.push(I32.astype(i8))

    def i32_load16_s(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i16 = SignedI16.from_bits(self.env.memory[addr : addr + 2])
        self.stack.push(I32.astype(i16))

    def i32_load16_u(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i16 = I16.from_bits(self.env.memory[addr : addr + 2])
        self.stack.push(I32.astype(i16))

    def i64_load8_s(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i8 = SignedI8.from_bits(self.env.memory[addr : addr + 1])
        self.stack.push(I64.astype(i8))

    def i64_load8_u(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i8 = I8.from_bits(self.env.memory[addr : addr + 1])
        self.stack.push(I64.astype(i8))

    def i64_load16_s(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i16 = SignedI16.from_bits(self.env.memory[addr : addr + 2])
        self.stack.push(I64.astype(i16))

    def i64_load16_u(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i16 = I16.from_bits(self.env.memory[addr : addr + 2])
        self.stack.push(I64.astype(i16))

    def i64_load32_s(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i32 = SignedI32.from_bits(self.env.memory[addr : addr + 4])
        self.stack.push(I64.astype(i32))

    def i64_load32_u(self, align: int, offset: int):
        a = self.stack.i32()
        addr = int(a + I32.from_int(offset))
        i32 = I32.from_bits(self.env.memory[addr : addr + 4])
        self.stack.push(I64.astype(i32))

    def i32_store(self, align: int, offset: int):
        a, addr = self.stack.i32(), self.stack.int()
        self.env.memory[addr : addr + 4] = a.to_bytes()[0:4]

    def i64_store(self, align: int, offset: int):
        a, addr = self.stack.i64(), self.stack.int()
        self.env.memory[addr : addr + 8] = a.to_bytes()[0:8]

    def f32_store(self, align: int, offset: int):
        a, addr = self.stack.f32(), self.stack.int()
        self.env.memory[addr : addr + 4] = a.to_bytes()[0:4]

    def f64_store(self, align: int, offset: int):
        a, addr = self.stack.f64(), self.stack.int()
        self.env.memory[addr : addr + 8] = a.to_bytes()[0:8]

    def i32_store8(self, align: int, offset: int):
        a, addr = self.stack.i32(), self.stack.int()
        self.env.memory[addr : addr + 1] = a.to_bytes()[0:1]

    def i32_store16(self, align: int, offset: int):
        a, addr = self.stack.i32(), self.stack.int()
        self.env.memory[addr : addr + 2] = a.to_bytes()[0:2]

    def i64_store8(self, align: int, offset: int):
        a, addr = self.stack.i64(), self.stack.int()
        self.env.memory[addr : addr + 1] = a.to_bytes()[0:1]

    def i64_store16(self, align: int, offset: int):
        a, addr = self.stack.i64(), self.stack.int()
        self.env.memory[addr : addr + 2] = a.to_bytes()[0:2]

    def i64_store32(self, align: int, offset: int):
        a, addr = self.stack.i64(), self.stack.int()
        self.env.memory[addr : addr + 4] = a.to_bytes()[0:4]

    def memory_size(self, index: int):
        a = len(self.env.memory) // 64 // 1024
        self.stack.push(I32.from_int(a))

    def memory_grow(self, index: int):
        a = self.stack.int()
        b = len(self.env.memory) // 64 // 1024
        self.env.memory.grow(64 * 1024 * a)
        self.stack.push(I32.from_int(b))

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

    def i32_div_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(I32.astype(sa / sb))

    def i32_div_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a / b)

    def i32_rem_s(self):
        b, a = self.stack.i32(), self.stack.i32()
        sb, sa = SignedI32.astype(b), SignedI32.astype(a)
        self.stack.push(I32.astype(sa % sb))

    def i32_rem_u(self):
        b, a = self.stack.i32(), self.stack.i32()
        self.stack.push(a % b)

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

    def i64_div_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(I64.astype(sa / sb))

    def i64_div_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a / b)

    def i64_rem_s(self):
        b, a = self.stack.i64(), self.stack.i64()
        sb, sa = SignedI64.astype(b), SignedI64.astype(a)
        self.stack.push(I64.astype(sa % sb))

    def i64_rem_u(self):
        b, a = self.stack.i64(), self.stack.i64()
        self.stack.push(a % b)

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

    def i32_trunc_f32_s(self):
        a = self.stack.f32()
        i32 = SignedI32.astype(trunc(a))
        self.stack.push(I32.astype(i32))

    def i32_trunc_f32_u(self):
        a = self.stack.f32()
        i32 = I32.astype(trunc(a))
        self.stack.push(i32)

    def i32_trunc_f64_s(self):
        a = self.stack.f64()
        i32 = SignedI32.astype(trunc(a))
        self.stack.push(I32.astype(i32))

    def i32_trunc_f64_u(self):
        a = self.stack.f64()
        i32 = I32.astype(trunc(a))
        self.stack.push(i32)

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

    def ref_null(self, type: int):
        self.stack.push(WasmOptimizer.get_ref_type(type).from_null())

    def ref_is_null(self):
        a = self.stack.ref()
        self.stack.push(I32.from_bool(a.is_none()))

    def ref_func(self, index: int):
        self.stack.push(FuncRef.from_value(index))

    def ref_as_non_null(self):
        pass

    def i64_trunc_f32_s(self):
        a = self.stack.f32()
        i64 = I64.from_value_with_clamp(trunc(a), SignedI64)
        self.stack.push(i64)

    def i64_trunc_f32_u(self):
        a = self.stack.f32()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, I64)
        self.stack.push(i64)

    def i64_trunc_f64_s(self):
        a = self.stack.f64()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, SignedI64)
        self.stack.push(I64.astype(i64))

    def i64_trunc_f64_u(self):
        a = self.stack.f64()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, I64)
        self.stack.push(i64)

    def i32_trunc_sat_f32_s(self):
        a = self.stack.f32()
        t = trunc(a)
        i32 = I32.from_value_with_clamp(t, SignedI32)
        self.stack.push(i32)

    def i32_trunc_sat_f32_u(self):
        a = self.stack.f32()
        t = trunc(a)
        i32 = I32.from_value_with_clamp(t, I32)
        self.stack.push(i32)

    def i32_trunc_sat_f64_s(self):
        a = self.stack.f64()
        t = trunc(a)
        i32 = I32.from_value_with_clamp(t, SignedI32)
        self.stack.push(I32.astype(i32))

    def i32_trunc_sat_f64(self):
        a = self.stack.f64()
        t = trunc(a)
        i32 = I32.from_value_with_clamp(t, I32)
        self.stack.push(i32)

    def i64_trunc_sat_f32_s(self):
        a = self.stack.f32()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, SignedI64)
        self.stack.push(i64)

    def i64_trunc_sat_f32(self):
        a = self.stack.f32()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, I64)
        self.stack.push(i64)

    def i64_trunc_sat_f64_s(self):
        a = self.stack.f64()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, SignedI64)
        self.stack.push(I64.astype(i64))

    def i64_trunc_sat_f64(self):
        a = self.stack.f64()
        t = trunc(a)
        i64 = I64.from_value_with_clamp(t, I64)
        self.stack.push(i64)

    def memory_init(self, index: int, index2: int):
        c, b, a = self.stack.int(), self.stack.int(), self.stack.int()
        memory = self.env.init_memory[index]
        self.env.memory[a : a + c] = memory[b : b + c]

    def data_drop(self, index: int):
        self.env.init_memory[index].drop()

    def memory_copy(self, index: int, index2: int):
        c, b, a = self.stack.int(), self.stack.int(), self.stack.int()
        self.env.memory[a : a + c] = self.env.memory[b : b + c]

    def memory_fill(self, index: int):
        c, b, a = self.stack.int(), self.stack.i32(), self.stack.int()
        value = I8.astype(b)
        self.env.memory[a : a + c] = value.value

    def table_init(self, index: int, index2: int):
        c, b, a = self.stack.int(), self.stack.int(), self.stack.int()
        elem = self.env.sections.element_section[index]
        table = self.env.sections.table_section[index2]
        ref = WasmOptimizer.get_ref_type(table.element_type)
        res = [ref.from_value(x) for x in elem.get_funcidx()[b : b + c]]
        self.env.tables[index2][a : a + c] = res

    def elem_drop(self, index: int):
        self.env.drop_elem[index] = True

    def table_copy(self, index: int, index2: int):
        c, b, a = self.stack.int(), self.stack.int(), self.stack.int()
        self.env.tables[index][a : a + c] = self.env.tables[index2][b : b + c]

    def table_grow(self, index: int):
        a = self.stack.int()
        _, table = self.env.get_table(index)
        b = self.stack.ref()
        self.stack.push(I32.from_int(len(table)))
        table[len(table) : len(table) + a] = [b for _ in range(a)]

    def table_size(self, index: int):
        self.stack.push(I32.from_int(len(self.env.tables[index])))

    def table_fill(self, index: int):
        c, b, a = self.stack.int(), self.stack.ref(), self.stack.int()
        table = self.env.tables[index]
        table[a : a + c] = [b for _ in range(int(c))]
