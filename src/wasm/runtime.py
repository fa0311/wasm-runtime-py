import logging

from wasm.spec import CodeSectionSpec
from wasm.struct import (
    CodeInstruction,
    CodeSection,
    ExportSection,
    FunctionSection,
    SectionBase,
    TypeSection,
)

from src.tools.logger import NestedLogger
from src.wasm.type.base import NumericType
from src.wasm.type.main import F32, F64, I32, LEB128


class WasmRuntime:
    """Wasmバイナリを実行するためのクラス"""

    type_section: list[TypeSection]
    function_section: list[FunctionSection]
    export_section: list[ExportSection]
    code_section: list[CodeSection]

    def __init__(self, data: list[SectionBase]):
        # セクションを分類する
        self.type_section = [x for x in data if isinstance(x, TypeSection)]
        self.function_section = [x for x in data if isinstance(x, FunctionSection)]
        self.export_section = [x for x in data if isinstance(x, ExportSection)]
        self.code_section = [x for x in data if isinstance(x, CodeSection)]

    def start(self, field: bytes, param: list[NumericType]):
        """エントリーポイントを実行する"""

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.export_section if fn.field == field][0]
        fn, _ = self.get_function(start.index)

        # ローカル変数を初期化して実行する
        locals_param = [NumericType(0) for _ in fn.local]
        locals = [*param, *locals_param]
        stack = CodeSectionRunner(self, fn.data, locals=locals)
        return stack

    def get_function(self, index: int) -> tuple[CodeSection, TypeSection]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        fn = self.function_section[index]
        type = self.type_section[fn.type]
        code = self.code_section[index]
        return code, type


class CodeSectionRunner(CodeSectionSpec):
    """Code Sectionのデータ構造"""

    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(
        self,
        parent: WasmRuntime,
        data: list[CodeInstruction],
        locals: list[NumericType],
    ):
        self.parent = parent
        self.data = data
        self.locals = locals

        self.stack: list[NumericType] = []
        self.block_stack: list[tuple] = []
        self.pointer = 0

    @logger.logger
    def run(self) -> list[NumericType]:
        while self.pointer < len(self.data):
            instruction = self.data[self.pointer]
            opcode = instruction.opcode
            args = instruction.args
            self.bind(self, opcode)(*args)
            self.logger.debug(f"run: {instruction}")

            self.pointer += 1
        return self.stack

    def skip(self):
        count = 0
        while self.data[self.pointer + count].opcode not in [0x0B, 0x05]:
            count += 1
        self.pointer += count
        # self.logger.debug(f"skip: {count} instructions")

    def i32_const(self, value: LEB128):
        self.stack.append(value)

    def push_f32(self, value: F32):
        self.stack.append(value)

    def push_f64(self, value: F64):
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
        self.stack.append(a == NumericType(0))

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

    def i32_clz(self):
        a = self.stack.pop()
        self.stack.append(a.clz())

    def i32_ctz(self):
        a = self.stack.pop()
        self.stack.append(a.ctz())

    def i32_popcnt(self):
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

    def i32_shl(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a << (b % I32(32)))

    def i32_shr_s(self):
        b, a = self.stack.pop(), self.stack.pop()
        sb, sa = b.to_signed(), a.to_signed()
        self.stack.append((sa >> (sb % I32(32))).to_unsigned())

    def i32_shr_u(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a >> (b % I32(32)))

    def i32_rotl(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append((a << (b % I32(32))) | (a >> (I32(32) - (b % I32(32)))))

    def i32_rotr(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append((a >> (b % I32(32))) | (a << (I32(32) - (b % I32(32)))))

    def if_(self, type: int):
        a = self.stack.pop()
        if not a:
            self.skip()
            self.pointer += 1

    def else_(self):
        self.skip()
        self.pointer += 1

    def br_if(self, count: int):
        a = self.stack.pop()
        if a:
            for _ in range(count):
                self.block_stack.pop()
                self.skip()
                self.pointer += 1
            self.skip()

    def br(self, count: int):
        for _ in range(count):
            self.block_stack.pop()
            self.skip()
            self.pointer += 1
        self.skip()

    def block(self, block_type: int):
        self.block_stack.append((0x02, self.pointer))

    def loop(self, block_type: int):
        self.block_stack.append((0x03, self.pointer))

    def block_end(self):
        if self.block_stack:
            opcode, pointer = self.block_stack[-1]
            if opcode in [0x03]:
                self.pointer = pointer
            elif opcode in [0x02]:
                pass
            else:
                raise Exception("unknown block type")
        else:
            pass

    def call(self, index: int):
        fn, fn_type = self.parent.get_function(index)
        param = [self.stack.pop() for _ in fn_type.params]
        locals_param = [0 for _ in fn.local]
        locals = [*param, *locals_param]
        runner = CodeSectionRunner(self.parent, fn.data.copy(), locals=locals)
        res = runner.run()
        self.stack.extend([res.pop() for _ in fn_type.returns])

    def drop(self):
        self.stack.pop()

    def return_(self):
        return self.stack
