import logging

from tools.byte import ByteReader
from tools.logger import NestedLogger

from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.struct import (
    CodeInstruction,
    CodeSection,
    ExportSection,
    FunctionSection,
    TypeSection,
    WasmSections,
)
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64, SignedI32, SignedI64


class WasmLoader:
    """Wasmバイナリを読み込むためのクラス"""

    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(self, data: bytes):
        self.data = ByteReader(data)

    @logger.logger
    def load(self) -> WasmSections:
        """Wasmバイナリを読み込んで解析する"""

        # マジックナンバーとバージョン番号を確認
        if self.data.read_bytes(4) != bytes([0, 97, 115, 109]):
            raise Exception("invalid magic number")

        # バージョン番号を確認
        if self.data.read_bytes(4) != bytes([1, 0, 0, 0]):
            raise Exception("invalid version number")

        # セクションを読み込む
        res = []
        while self.data.has_next():
            id = self.data.read_byte()
            size = self.data.read_leb128()
            data = self.data.read_bytes(size)
            self.logger.debug(f"id: {id}, size: {size}")
            if id == 1:
                res.extend(self.type_section(data))
            elif id == 3:
                res.extend(self.function_section(data))
            elif id == 10:
                res.extend(self.code_section(data))
            elif id == 7:
                res.extend(self.export_section(data))
            else:
                self.logger.error(f"unknown id: {id}")

        sections = WasmSections(
            type_section=[x for x in res if isinstance(x, TypeSection)],
            function_section=[x for x in res if isinstance(x, FunctionSection)],
            code_section=[x for x in res if isinstance(x, CodeSection)],
            export_section=[x for x in res if isinstance(x, ExportSection)],
        )

        # 解析結果を返す
        return sections

    @logger.logger
    def type_section(self, data: ByteReader) -> list[TypeSection]:
        """Type Sectionを読み込む"""

        # Type Sectionの数を読み込む
        type_count = data.read_leb128()
        self.logger.debug(f"type count: {type_count}")

        # Type Sectionのデータを読み込む
        res: list[TypeSection] = []
        for _ in range(type_count):
            form = data.read_byte()
            param_count = data.read_leb128()
            params = [data.read_byte() for _ in range(param_count)]
            return_count = data.read_leb128()
            returns = [data.read_byte() for _ in range(return_count)]
            section = TypeSection(form=form, params=params, returns=returns)
            self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def function_section(self, data: ByteReader) -> list[FunctionSection]:
        """Function Sectionを読み込む"""

        # Function Sectionの数を読み込む
        function_count = data.read_leb128()
        self.logger.debug(f"function count: {function_count}")

        # Function Sectionのデータを読み込む
        res: list[FunctionSection] = []
        for _ in range(function_count):
            type = data.read_leb128()
            section = FunctionSection(type=type)
            self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def code_section(self, data: ByteReader) -> list[CodeSection]:
        """Code Sectionを読み込む"""

        # Code Sectionの数を読み込む
        code_count = data.read_leb128()
        self.logger.debug(f"code count: {code_count}")

        # Code Sectionのデータを読み込む
        res: list[CodeSection] = []
        for _ in range(code_count):
            body_size = data.read_leb128()
            code = data.read_bytes(body_size)
            local = self.code_section_local(code)
            instructions = self.code_section_instructions(code)
            self.logger.debug(f"body size: {body_size}")
            section = CodeSection(data=instructions, local=local)
            self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def code_section_instructions(self, data: ByteReader) -> list[CodeInstruction]:
        res: list[CodeInstruction] = []
        while data.has_next():
            opcode = data.read_byte()
            fn = CodeSectionSpecHelper.mapped(opcode)

            annotations: list[type] = [e for e in fn.__annotations__.values()]

            args: list = []

            for annotation in annotations:
                if annotation == int:
                    args.append(data.read_byte())
                elif annotation == I32:
                    args.append(SignedI32.from_int(data.read_sleb128()).to_unsigned())
                elif annotation == I64:
                    args.append(SignedI64.from_int(data.read_sleb128()).to_unsigned())
                elif annotation == F32:
                    args.append(F32.from_str(data.read_bytes(4).data))
                elif annotation == F64:
                    args.append(F64.from_str(data.read_bytes(8).data))
                else:
                    raise Exception("invalid type")
            instruction = CodeInstruction(opcode=opcode, args=args)
            self.logger.debug(instruction)
            res.append(instruction)
        return res

    @logger.logger
    def code_section_local(self, data: ByteReader) -> list[int]:
        """Code Sectionのローカル変数を読み込む"""

        # ローカル変数の数を読み込む
        count = data.read_leb128()
        self.logger.debug(f"local count: {count}")

        # ローカル変数のデータを読み込む
        local: list[int] = []
        for _ in range(count):
            local_count = data.read_leb128()
            local_type = data.read_byte()
            local.extend([local_type] * local_count)
            self.logger.debug(f"type: {local_type} * {local_count}")

        # 解析結果を返す
        return local

    @logger.logger
    def export_section(self, data: ByteReader) -> list[ExportSection]:
        """Export Sectionを読み込む"""

        # Export Sectionの数を読み込む
        export_count = data.read_leb128()
        self.logger.debug(f"export count: {export_count}")

        # Export Sectionのデータを読み込む
        res: list[ExportSection] = []
        for _ in range(export_count):
            field_len = data.read_leb128()
            field = data.read_bytes(field_len)
            kind = data.read_byte()
            index = data.read_leb128()
            section = ExportSection(field=field, kind=kind, index=index)
            self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res
