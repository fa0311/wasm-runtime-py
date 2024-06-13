import logging
from typing import Callable

from tools.logger import NestedLogger
from wasm.struct import (
    CodeInstruction,
    CodeSection,
    ExportSection,
    FunctionSection,
    SectionBase,
    TypeSection,
)
from wasm.type import F32, F64, LEB128, NumericType


class WasmRuntime:
    """Wasmバイナリを実行するためのクラス"""

    logger = NestedLogger(logging.getLogger(__name__))
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
        self.logger.logging.info(f"stack: {stack}")
        return stack.run()

    def get_function(self, index: int) -> tuple[CodeSection, TypeSection]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        fn = self.function_section[index]
        type = self.type_section[fn.type]
        code = self.code_section[fn.type]
        return code, type


class CodeSectionHelper:
    mapped: dict[int, Callable[..., None]] = {}

    @staticmethod
    def factory(*opcodes: int):
        """Code Sectionのヘルパー関数"""

        def decorator(func):
            for opcode in opcodes:
                CodeSectionHelper.mapped[opcode] = func

            def error(*args):
                raise NotImplementedError(f"opcode: {opcode:02X}")

            return error

        return decorator


class CodeSectionRunner:
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

    @CodeSectionHelper.factory(0x41, 0x42)
    def push_leb123(self, value: LEB128):
        self.stack.append(value)

    @CodeSectionHelper.factory(0x43)
    def push_f32(self, value: F32):
        self.stack.append(value)

    @CodeSectionHelper.factory(0x44)
    def push_f64(self, value: F64):
        self.stack.append(value)

    @CodeSectionHelper.factory(0x20)
    def local_get(self, index: int):
        self.stack.append(self.locals[index])

    @CodeSectionHelper.factory(0x21)
    def local_set(self, index: int):
        self.locals[index] = self.stack.pop()

    @CodeSectionHelper.factory(0x22)
    def local_tee(self, index: int):
        self.locals[index] = self.stack[-1]

    @CodeSectionHelper.factory(0x6A, 0x7C, 0x92, 0xA0)
    def add(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a + b)

    @CodeSectionHelper.factory(0x6B, 0x7D, 0x93, 0xA1)
    def sub(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a - b)

    @CodeSectionHelper.factory(0x6C, 0x7E, 0x94, 0xA2)
    def mul(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a * b)

    @CodeSectionHelper.factory(0x6D, 0x6E, 0x7F, 0x80, 0x95, 0xA3)
    def div(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a / b)

    @CodeSectionHelper.factory(0x6F, 0x70, 0x81, 0x82)
    def rem(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a % b)

    @CodeSectionHelper.factory(0x46, 0x51, 0x5B, 0x61)
    def eq(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a == b)

    @CodeSectionHelper.factory(0x47, 0x52, 0x5C, 0x62)
    def ne(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a != b)

    @CodeSectionHelper.factory(0x45, 0x50)
    def eqz(self):
        a = self.stack.pop()
        self.stack.append(a == NumericType(0))

    @CodeSectionHelper.factory(0x4A, 0x4B, 0x55, 0x56, 0x5E, 0x64)
    def gt(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a > b)

    @CodeSectionHelper.factory(0x4E, 0x4F, 0x59, 0x5A, 0x60, 0x66)
    def ge(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a >= b)

    @CodeSectionHelper.factory(0x48, 0x49, 0x53, 0x54, 0x5D, 0x63)
    def lt(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a < b)

    @CodeSectionHelper.factory(0x4C, 0x4D, 0x57, 0x58, 0x5F, 0x65)
    def le(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a <= b)

    @CodeSectionHelper.factory(0x71, 0x83)
    def and_(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a & b)

    @CodeSectionHelper.factory(0x72, 0x84)
    def or_(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a | b)

    @CodeSectionHelper.factory(0x73, 0x85)
    def xor(self):
        b, a = self.stack.pop(), self.stack.pop()
        self.stack.append(a ^ b)

    @CodeSectionHelper.factory(0x04)
    def if_(self, type: int):
        a = self.stack.pop()
        if not a:
            self.skip()
            self.pointer += 1

    @CodeSectionHelper.factory(0x05)
    def else_(self):
        self.skip()
        self.pointer += 1

    @CodeSectionHelper.factory(0x0D)
    def br_if(self, count: int):
        a = self.stack.pop()
        if a:
            for _ in range(count):
                self.block_stack.pop()
                self.skip()
                self.pointer += 1
            self.skip()

    @CodeSectionHelper.factory(0x0C)
    def br(self, count: int):
        for _ in range(count):
            self.block_stack.pop()
            self.skip()
            self.pointer += 1
        self.skip()

    @CodeSectionHelper.factory(0x02)
    def block(self, block_type: int):
        self.block_stack.append((0x02, self.pointer))
        self.pointer += 1

    @CodeSectionHelper.factory(0x03)
    def loop(self, block_type: int):
        self.block_stack.append((0x03, self.pointer))
        self.pointer += 1

    @CodeSectionHelper.factory(0x0B)
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

    @CodeSectionHelper.factory(0x10)
    def call(self, index: int):
        fn, fn_type = self.parent.get_function(index)
        param = [self.stack.pop() for _ in fn_type.params]
        locals_param = [0 for _ in fn.local]
        locals = [*param, *locals_param]
        runner = CodeSectionRunner(self.parent, fn.data.copy(), locals=locals)
        res = runner.run()
        self.stack.extend([res.pop() for _ in fn_type.returns])

    @CodeSectionHelper.factory(0x1A)
    def drop(self):
        self.stack.pop()

    @CodeSectionHelper.factory(0x0F)
    def return_(self):
        return self.stack

    def run(self) -> list[NumericType]:
        while self.pointer < len(self.data):
            instruction = self.data[self.pointer]
            self.logger.debug(f"run: {instruction}")
            opcode = instruction.opcode
            args = instruction.args
            CodeSectionHelper.mapped[opcode](self, *args)
            self.pointer += 1
        return self.stack

    def skip(self):
        count = 0
        while self.data[self.pointer + count].opcode not in [0x0B, 0x05]:
            count += 1
        self.pointer += count
        self.logger.debug(f"skip: {count} bytes")

    # @logger.logger
    # def run(self, data: ByteReader, locals: list[int] = []):
    #     """Code Sectionを実行する"""

    #     # 変数スタックを初期化する
    #     stack = []

    #     # ブロックスタックを初期化する
    #     block: list[tuple] = []

    #     while data.has_next():
    #         opcode = data.read_byte()

    #         if opcode in [0x41, 0x42]:
    #             value = data.read_leb128()
    #             stack.append(value)
    #             self.logger.debug(f"push: {value}")
    #         elif opcode in [0x43]:
    #             value = data.read_f32()
    #             stack.append(value)
    #             self.logger.debug(f"push: {value}")
    #         elif opcode in [0x44]:
    #             value = data.read_f64()
    #             stack.append(value)
    #             self.logger.debug(f"push: {value}")

    #         elif opcode in [0x20]:
    #             index = data.read_byte()
    #             stack.append(locals[index])
    #             self.logger.debug(f"local.get: {index}")
    #         elif opcode in [0x21]:
    #             index = data.read_byte()
    #             locals[index] = stack.pop()
    #             self.logger.debug(f"local.set: {index}")
    #         elif opcode in [0x22]:
    #             index = data.read_byte()
    #             locals[index] = stack[-1]
    #             self.logger.debug(f"local.tee: {index}")

    #         elif opcode in [0x6A, 0x7C, 0x92, 0xA0]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a + b)
    #             self.logger.debug(f"add: {a} + {b}")
    #         elif opcode in [0x6B, 0x7D, 0x93, 0xA1]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a - b)
    #             self.logger.debug(f"sub: {a} - {b}")
    #         elif opcode in [0x6C, 0x7E, 0x94, 0xA2]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a * b)
    #             self.logger.debug(f"mul: {a} * {b}")
    #         elif opcode in [0x6D, 0x6E, 0x7F, 0x80, 0x95, 0xA3]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a / b)
    #             self.logger.debug(f"div: {a} / {b}")
    #         elif opcode in [0x6F, 0x70, 0x81, 0x82]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a % b)
    #             self.logger.debug(f"rem: {a} % {b}")

    #         elif opcode in [0x46, 0x51, 0x5B, 0x61]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a == b)
    #             self.logger.debug(f"eq: {a} == {b}")
    #         elif opcode in [0x47, 0x52, 0x5C, 0x62]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a != b)
    #             self.logger.debug(f"ne: {a} != {b}")
    #         elif opcode in [0x45, 0x50]:
    #             a = stack.pop()
    #             stack.append(a == 0)
    #             self.logger.debug(f"eqz: {a} == 0")
    #         elif opcode in [0x4A, 0x4B, 0x55, 0x56, 0x5E, 0x64]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a > b)
    #             self.logger.debug(f"gt: {a} > {b}")
    #         elif opcode in [0x4E, 0x4F, 0x59, 0x5A, 0x60, 0x66]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a >= b)
    #             self.logger.debug(f"ge: {a} >= {b}")

    #         elif opcode in [0x48, 0x49, 0x53, 0x54, 0x5D, 0x63]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a < b)
    #             self.logger.debug(f"lt: {a} < {b}")
    #         elif opcode in [0x4C, 0x4D, 0x57, 0x58, 0x5F, 0x65]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a <= b)
    #             self.logger.debug(f"le: {a} <= {b}")

    #         elif opcode in [0x71, 0x83]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a & b)
    #             self.logger.debug(f"and: {a} & {b}")
    #         elif opcode in [0x72, 0x84]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a | b)
    #             self.logger.debug(f"or: {a} | {b}")
    #         elif opcode in [0x73, 0x85]:
    #             b, a = stack.pop(), stack.pop()
    #             stack.append(a ^ b)
    #             self.logger.debug(f"xor: {a} ^ {b}")

    #         elif opcode in [0x04]:
    #             # もし条件がFalseならelseかendまでスキップする
    #             a = stack.pop()
    #             type = data.read_leb128()
    #             self.logger.debug(f"if: {a} {type:02x}")
    #             if not a:
    #                 self.skip(data)
    #                 data.read_byte()
    #         elif opcode in [0x05]:
    #             # elseならendまでスキップする
    #             # if が False の場合はここに到達しない
    #             self.logger.debug("else")
    #             self.skip(data)
    #             data.read_byte()
    #         elif opcode in [0x0D]:
    #             # もし条件がFalseならn回endまでスキップする
    #             a = stack.pop()
    #             count = data.read_leb128()
    #             self.logger.debug(f"br_if: {a} {count}")
    #             if a:
    #                 for _ in range(count):
    #                     block.pop()
    #                     self.skip(data)
    #                     data.read_byte()
    #                 self.skip(data)
    #         elif opcode in [0x0C]:
    #             # n回endまでスキップする
    #             count = data.read_leb128()
    #             self.logger.debug(f"br: {count}")
    #             for _ in range(count):
    #                 block.pop()
    #                 self.skip(data)
    #                 data.read_byte()
    #             self.skip(data)
    #         elif opcode in [0x02]:
    #             # ブロックを開始する
    #             # ブロックの種類とポインタを保存する
    #             block_type = data.read_leb128()
    #             block.append((opcode, data.pointer))
    #             self.logger.debug(f"block: {block_type:02x}")
    #         elif opcode in [0x03]:
    #             # ループを開始する
    #             # ループの種類とポインタを保存する
    #             block_type = data.read_leb128()
    #             block.append((opcode, data.pointer))
    #             self.logger.debug(f"loop: {block_type:02x}")
    #         elif opcode in [0x0B]:
    #             # ブロックまたはループを終了する
    #             # ブロックまたはループの種類に応じて処理を分岐する
    #             if block:
    #                 opcode, data_pointer = block[-1]
    #                 if opcode in [0x03]:
    #                     data.pointer = data_pointer
    #                     self.logger.debug("loop end")
    #                 elif opcode in [0x02]:
    #                     self.logger.debug("block end")
    #                 else:
    #                     raise Exception("unknown block type")
    #             else:
    #                 self.logger.debug("end")
    #         elif opcode in [0x10]:
    #             index = data.read_leb128()
    #             self.logger.debug(f"call: {index}")
    #             fn, fn_type = self.get_function(index)
    #             param = [stack.pop() for _ in fn_type.params]
    #             locals_param = [0 for _ in fn.local]
    #             res = self.run(fn.data.copy(), locals=[*param, *locals_param])
    #             stack.extend([res.pop() for _ in fn_type.returns])
    #         elif opcode in [0x1A]:
    #             a = stack.pop()
    #             self.logger.debug(f"drop: {a}")
    #         elif opcode in [0x0F]:
    #             self.logger.debug(f"return: {stack}")
    #             return stack
    #         else:
    #             self.logger.error(f"unknown opcode: {opcode:02X}")

    #     self.logger.debug(f"return: {stack}")
    #     return stack

    # def skip(self, data: ByteReader):
    #     count = 0
    #     while data.read_byte(read_only=True) not in [0x0B, 0x05]:
    #         data.read_byte()
    #         count += 1
    #     self.logger.debug(f"skip: {count} bytes")
