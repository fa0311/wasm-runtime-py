import logging
from typing import Union

from tools.byte import ByteReader
from tools.logger import NestedLogger
from wasm.struct import CodeSection, ExportSection, FunctionSection, TypeSection


class WasmRuntime:
    """Wasmバイナリを実行するためのクラス"""

    logger = NestedLogger(logging.getLogger(__name__))
    type_section: list[TypeSection]
    function_section: list[FunctionSection]
    export_section: list[ExportSection]
    code_section: list[CodeSection]

    def __init__(self, data: list[Union[CodeSection, ExportSection]]):
        # セクションを分類する
        self.type_section = [x for x in data if isinstance(x, TypeSection)]
        self.function_section = [x for x in data if isinstance(x, FunctionSection)]
        self.export_section = [x for x in data if isinstance(x, ExportSection)]
        self.code_section = [x for x in data if isinstance(x, CodeSection)]

    def start(self, field: bytes = b"_start", param: list[int] = []):
        """エントリーポイントを実行する"""

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.export_section if fn.field == field][0]
        fn, _ = self.get_function(start.index)

        # ローカル変数を初期化して実行する
        locals_param = [0 for _ in fn.local]
        stack = self.run(fn.data.copy(), locals=[*param, *locals_param])
        self.logger.logging.info(f"stack: {stack}")
        return stack

    def get_function(self, index: int) -> tuple[CodeSection, TypeSection]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        fn = self.function_section[index]
        type = self.type_section[fn.type]
        code = self.code_section[fn.type]
        return code, type

    @logger.logger
    def run(self, data: ByteReader, locals: list[int] = []):
        """Code Sectionを実行する"""

        # 変数スタックを初期化する
        stack = []

        # ブロックスタックを初期化する
        block: list[tuple] = []

        while data.has_next():
            opcode = data.read_byte()

            if opcode in [0x41, 0x42]:
                value = data.read_leb128()
                stack.append(value)
                self.logger.debug(f"push: {value}")
            elif opcode in [0x43]:
                value = data.read_f32()
                stack.append(value)
                self.logger.debug(f"push: {value}")
            elif opcode in [0x44]:
                value = data.read_f64()
                stack.append(value)
                self.logger.debug(f"push: {value}")
            elif opcode in [0x20]:
                index = data.read_byte()
                stack.append(locals[index])
                self.logger.debug(f"local.get: {index}")
            elif opcode in [0x21]:
                index = data.read_byte()
                locals[index] = stack.pop()
                self.logger.debug(f"local.set: {index}")
            elif opcode in [0x22]:
                index = data.read_byte()
                locals[index] = stack[-1]
                self.logger.debug(f"local.tee: {index}")
            elif opcode in [0x6A, 0x7C, 0x92, 0xA0]:
                b, a = stack.pop(), stack.pop()
                stack.append(a + b)
                self.logger.debug(f"add: {a} + {b}")
            elif opcode in [0x6B, 0x7D, 0x93, 0xA1]:
                b, a = stack.pop(), stack.pop()
                stack.append(a - b)
                self.logger.debug(f"sub: {a} - {b}")
            elif opcode in [0x6C, 0x7E, 0x94, 0xA2]:
                b, a = stack.pop(), stack.pop()
                stack.append(a * b)
                self.logger.debug(f"mul: {a} * {b}")
            elif opcode in [0x6D, 0x6E, 0x7F, 0x80, 0x95, 0xA3]:
                b, a = stack.pop(), stack.pop()
                stack.append(a / b)
                self.logger.debug(f"div: {a} / {b}")
            elif opcode in [0x6F, 0x70, 0x81, 0x82]:
                b, a = stack.pop(), stack.pop()
                stack.append(a % b)
                self.logger.debug(f"rem: {a} % {b}")

            elif opcode in [0x46, 0x51, 0x5B, 0x61]:
                b, a = stack.pop(), stack.pop()
                stack.append(a == b)
                self.logger.debug(f"eq: {a} == {b}")
            elif opcode in [0x47, 0x52, 0x5C, 0x62]:
                b, a = stack.pop(), stack.pop()
                stack.append(a != b)
                self.logger.debug(f"ne: {a} != {b}")
            elif opcode in [0x45, 0x50]:
                a = stack.pop()
                stack.append(a == 0)
                self.logger.debug(f"eqz: {a} == 0")
            elif opcode in [0x4A, 0x4B, 0x55, 0x56, 0x5E, 0x64]:
                b, a = stack.pop(), stack.pop()
                stack.append(a > b)
                self.logger.debug(f"gt: {a} > {b}")
            elif opcode in [0x4E, 0x4F, 0x59, 0x5A, 0x60, 0x66]:
                b, a = stack.pop(), stack.pop()
                stack.append(a >= b)
                self.logger.debug(f"ge: {a} >= {b}")

            elif opcode in [0x48, 0x49, 0x53, 0x54, 0x5D, 0x63]:
                b, a = stack.pop(), stack.pop()
                stack.append(a < b)
                self.logger.debug(f"lt: {a} < {b}")
            elif opcode in [0x4C, 0x4D, 0x57, 0x58, 0x5F, 0x65]:
                b, a = stack.pop(), stack.pop()
                stack.append(a <= b)
                self.logger.debug(f"le: {a} <= {b}")

            elif opcode in [0x71, 0x83]:
                b, a = stack.pop(), stack.pop()
                stack.append(a & b)
                self.logger.debug(f"and: {a} & {b}")
            elif opcode in [0x72, 0x84]:
                b, a = stack.pop(), stack.pop()
                stack.append(a | b)
                self.logger.debug(f"or: {a} | {b}")
            elif opcode in [0x73, 0x85]:
                b, a = stack.pop(), stack.pop()
                stack.append(a ^ b)
                self.logger.debug(f"xor: {a} ^ {b}")

            elif opcode in [0x04]:
                # もし条件がFalseならelseかendまでスキップする
                a = stack.pop()
                type = data.read_leb128()
                self.logger.debug(f"if: {a} {type:02x}")
                if not a:
                    self.skip(data)
                    data.read_byte()
            elif opcode in [0x05]:
                # elseならendまでスキップする
                # if が False の場合はここに到達しない
                self.logger.debug("else")
                self.skip(data)
                data.read_byte()
            elif opcode in [0x0D]:
                # もし条件がFalseならn回endまでスキップする
                a = stack.pop()
                count = data.read_leb128()
                self.logger.debug(f"br_if: {a} {count}")
                if a:
                    for _ in range(count):
                        block.pop()
                        self.skip(data)
                        data.read_byte()
                    self.skip(data)
            elif opcode in [0x0C]:
                # n回endまでスキップする
                count = data.read_leb128()
                self.logger.debug(f"br: {count}")
                for _ in range(count):
                    block.pop()
                    self.skip(data)
                    data.read_byte()
                self.skip(data)
            elif opcode in [0x02]:
                # ブロックを開始する
                # ブロックの種類とポインタを保存する
                block_type = data.read_leb128()
                block.append((opcode, data.pointer))
                self.logger.debug(f"block: {block_type:02x}")
            elif opcode in [0x03]:
                # ループを開始する
                # ループの種類とポインタを保存する
                block_type = data.read_leb128()
                block.append((opcode, data.pointer))
                self.logger.debug(f"loop: {block_type:02x}")
            elif opcode in [0x0B]:
                # ブロックまたはループを終了する
                # ブロックまたはループの種類に応じて処理を分岐する
                if block:
                    opcode, data_pointer = block[-1]
                    if opcode in [0x03]:
                        data.pointer = data_pointer
                        self.logger.debug("loop end")
                    elif opcode in [0x02]:
                        self.logger.debug("block end")
                    else:
                        raise Exception("unknown block type")
                else:
                    self.logger.debug("end")
            elif opcode in [0x10]:
                index = data.read_leb128()
                self.logger.debug(f"call: {index}")
                fn, fn_type = self.get_function(index)
                param = [stack.pop() for _ in fn_type.params]
                locals_param = [0 for _ in fn.local]
                res = self.run(fn.data.copy(), locals=[*param, *locals_param])
                stack.extend([res.pop() for _ in fn_type.returns])
            elif opcode in [0x1A]:
                a = stack.pop()
                self.logger.debug(f"drop: {a}")
            elif opcode in [0x0F]:
                self.logger.debug(f"return: {stack}")
                return stack
            else:
                self.logger.error(f"unknown opcode: {opcode:02X}")

        self.logger.debug(f"return: {stack}")
        return stack

    def skip(self, data: ByteReader):
        count = 0
        while data.read_byte(read_only=True) not in [0x0B, 0x05]:
            data.read_byte()
            count += 1
        self.logger.debug(f"skip: {count} bytes")
