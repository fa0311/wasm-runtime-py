import logging
from typing import TypeVar

from src.tools.byte import ByteReader
from src.tools.logger import NestedLogger
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import BlockType
from src.wasm.loader.struct import (
    CodeInstruction,
    CodeSection,
    DataSection,
    ElementSection,
    ExportSection,
    FunctionSection,
    GlobalSection,
    ImportSection,
    MemorySection,
    ModeActive,
    TableSection,
    TypeSection,
    WasmSections,
)
from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I32, I64, SignedI32, SignedI64


class WasmLoader:
    """Wasmバイナリを読み込むためのクラス"""

    logger = NestedLogger(logging.getLogger(__name__))
    T = TypeVar("T")

    @logger.logger
    def load(self, bin: bytes) -> WasmSections:
        """Wasmバイナリを読み込んで解析する"""
        data = ByteReader(bin)

        # マジックナンバーとバージョン番号を確認
        if data.read_bytes(4) != bytes([0, 97, 115, 109]):
            raise Exception("invalid magic number")

        # バージョン番号を確認
        if data.read_bytes(4) != bytes([1, 0, 0, 0]):
            raise Exception("invalid version number")

        # セクションを読み込む
        res = []
        while data.has_next():
            id = data.read_byte()
            size = data.read_leb128()
            section = data.read_bytes(size)
            assert self.logger.debug(f"id: {id}, size: {size}")
            if id == 2:
                res.extend(self.import_section(section))
            elif id == 1:
                res.extend(self.type_section(section))
            elif id == 3:
                res.extend(self.function_section(section))
            elif id == 4:
                res.extend(self.table_section(section))
            elif id == 5:
                res.extend(self.memory_section(section))
            elif id == 6:
                res.extend(self.global_section(section))
            elif id == 9:
                res.extend(self.element_section(section))
            elif id == 10:
                res.extend(self.code_section(section))
            elif id == 7:
                res.extend(self.export_section(section))
            elif id == 11:
                res.extend(self.data_section(section))
            else:
                assert self.logger.error(f"unknown id: {id}")

        sections = WasmSections(
            import_section=[x for x in res if isinstance(x, ImportSection)],
            type_section=[x for x in res if isinstance(x, TypeSection)],
            function_section=[x for x in res if isinstance(x, FunctionSection)],
            table_section=[x for x in res if isinstance(x, TableSection)],
            memory_section=[x for x in res if isinstance(x, MemorySection)],
            global_section=[x for x in res if isinstance(x, GlobalSection)],
            element_section=[x for x in res if isinstance(x, ElementSection)],
            code_section=[x for x in res if isinstance(x, CodeSection)],
            export_section=[x for x in res if isinstance(x, ExportSection)],
            data_section=[x for x in res if isinstance(x, DataSection)],
        )

        # 解析結果を返す
        return sections

    @logger.logger
    def import_section(self, data: ByteReader) -> list:
        """Import Sectionを読み込む"""

        # Import Sectionの数を読み込む
        count = data.read_leb128()

        assert self.logger.debug(f"import count: {count}")

        res: list["ImportSection"] = []

        for _ in range(count):
            module = data.read_bytes(data.read_leb128())
            name = data.read_bytes(data.read_leb128())
            kind = data.read_byte()
            _ = data.read_byte()
            res.append(ImportSection(module=module, name=name, kind=kind))

        return res

    @logger.logger
    def type_section(self, data: ByteReader) -> list[TypeSection]:
        """Type Sectionを読み込む"""

        # Type Sectionの数を読み込む
        type_count = data.read_leb128()
        assert self.logger.debug(f"type count: {type_count}")

        # Type Sectionのデータを読み込む
        res: list[TypeSection] = []
        for _ in range(type_count):
            form = data.read_byte()
            param_count = data.read_leb128()
            params = [data.read_byte() for _ in range(param_count)]
            return_count = data.read_leb128()
            returns = [data.read_byte() for _ in range(return_count)]
            section = TypeSection(form=form, params=params, returns=returns)
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def function_section(self, data: ByteReader) -> list[FunctionSection]:
        """Function Sectionを読み込む"""

        # Function Sectionの数を読み込む
        function_count = data.read_leb128()
        assert self.logger.debug(f"function count: {function_count}")

        # Function Sectionのデータを読み込む
        res: list[FunctionSection] = []
        for _ in range(function_count):
            type = data.read_leb128()
            section = FunctionSection(type=type)
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def table_section(self, data: ByteReader) -> list[TableSection]:
        """Table Sectionを読み込む"""

        # Table Sectionの数を読み込む
        table_count = data.read_leb128()
        assert self.logger.debug(f"table count: {table_count}")

        # Table Sectionのデータを読み込む
        res: list[TableSection] = []
        for _ in range(table_count):
            element_type = data.read_byte()
            limit_type = data.read_byte()

            if limit_type == 0:
                min = data.read_leb128()
                max = None
            elif limit_type == 1:
                min = data.read_leb128()
                max = data.read_leb128()
            else:
                raise Exception("invalid limit type")
            section = TableSection(
                element_type=element_type,
                limits_min=min,
                limits_max=max,
            )
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def memory_section(self, data: ByteReader) -> list[MemorySection]:
        """Memory Sectionを読み込む"""

        # Memory Sectionの数を読み込む
        memory_count = data.read_leb128()
        assert self.logger.debug(f"memory count: {memory_count}")

        # Memory Sectionのデータを読み込む
        res: list[MemorySection] = []
        for _ in range(memory_count):
            limit_type = data.read_byte()
            if limit_type == 0:
                min = data.read_leb128()
                max = None
            elif limit_type == 1:
                min = data.read_leb128()
                max = data.read_leb128()
            else:
                raise Exception("invalid limit type")
            section = MemorySection(limits_min=min, limits_max=max)
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def global_section(self, data: ByteReader) -> list[GlobalSection]:
        """Global Sectionを読み込む"""

        # Global Sectionの数を読み込む
        global_count = data.read_leb128()
        assert self.logger.debug(f"global count: {global_count}")

        # Global Sectionのデータを読み込む
        res: list[GlobalSection] = []
        for _ in range(global_count):
            content_type = data.read_byte()
            mutable = data.read_byte()
            init = self.code_section_instructions(data)
            section = GlobalSection(type=content_type, mutable=mutable, init=init)
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def element_section(self, data: ByteReader) -> list[ElementSection]:
        """Element Sectionを読み込む"""

        # Element Sectionの数を読み込む
        element_count = data.read_leb128()
        assert self.logger.debug(f"element count: {element_count}")

        # Element Sectionのデータを読み込む
        res: list[ElementSection] = []

        for _ in range(element_count):
            elem = data.read_byte()  # Elementのモード

            if elem == 0:  # Active
                offset = self.code_section_instructions(data)
                count = data.read_leb128()
                funcidx = [data.read_leb128() for _ in range(count)]
                active = ModeActive(table=0, offset=offset)
                section = ElementSection(elem=elem, type=0x70, funcidx=funcidx, active=active, ref=None)
                res.append(section)
            elif elem == 1:  # Passive
                type = data.read_byte()
                count = data.read_leb128()
                funcidx = [data.read_leb128() for _ in range(count)]
                section = ElementSection(elem=elem, type=type, funcidx=funcidx, active=None, ref=None)
                res.append(section)
            elif elem == 2:  # Active
                table = data.read_leb128()
                offset = self.code_section_instructions(data)
                type = data.read_byte()
                count = data.read_leb128()
                funcidx = [data.read_leb128() for _ in range(count)]
                active = ModeActive(table=table, offset=offset)
                section = ElementSection(elem=elem, type=type, funcidx=funcidx, active=active, ref=None)
                res.append(section)
            elif elem == 3:  # Declarative
                type = data.read_byte()
                count = data.read_leb128()
                funcidx = [data.read_leb128() for _ in range(count)]
                section = ElementSection(elem=elem, type=type, funcidx=funcidx, active=None, ref=None)
                res.append(section)
            elif elem == 5:  # Passive
                type = data.read_byte()
                ref = self.code_section_instructions(data)
                section = ElementSection(elem=elem, type=type, funcidx=None, active=None, ref=ref)
                res.append(section)
            else:
                raise Exception("invalid elem_type")

            assert self.logger.debug(section)

        # 解析結果を返す
        return res

    @logger.logger
    def code_section(self, data: ByteReader) -> list[CodeSection]:
        """Code Sectionを読み込む"""

        # Code Sectionの数を読み込む
        code_count = data.read_leb128()
        assert self.logger.debug(f"code count: {code_count}")

        # Code Sectionのデータを読み込む
        res: list[CodeSection] = []
        for _ in range(code_count):
            body_size = data.read_leb128()
            assert self.logger.debug(f"body size: {body_size}")
            local = self.code_section_local(data)
            instructions = self.code_section_instructions(data)
            section = CodeSection(data=instructions, local=local)
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def code_section_instructions(self, data: ByteReader) -> list[CodeInstruction]:
        """expr を読み込む"""
        res: list[CodeInstruction] = []
        stack = 0
        while stack >= 0:
            opcode = data.read_byte()
            if CodeSectionSpecHelper.is_prefix(opcode):
                opcode = (opcode << 8) | data.read_byte()

            fn = CodeSectionSpecHelper.mapped(opcode)
            block_type = CodeSectionSpecHelper.get_block_type(opcode)
            if block_type == BlockType.START:
                stack += 1
            elif block_type == BlockType.END:
                stack -= 1

            annotations: list[type] = [e for e in fn.__annotations__.values()]

            args: list = []

            for annotation in annotations:
                if annotation == int:  # noqa: E721
                    args.append(data.read_leb128())
                elif annotation == I32:
                    args.append(I32.astype(SignedI32.from_int(data.read_sleb128())))
                elif annotation == I64:
                    args.append(I64.astype(SignedI64.from_int(data.read_sleb128())))
                elif annotation == F32:
                    args.append(F32.from_bits(data.read_f32()))
                elif annotation == F64:
                    args.append(F64.from_bits(data.read_f64()))
                elif annotation == list[int]:
                    count = data.read_leb128()
                    args.append([data.read_byte() for _ in range(count + 1)])
                else:
                    raise Exception("invalid type")
            instruction = CodeInstruction(opcode=opcode, args=args)
            assert self.logger.debug(instruction)
            res.append(instruction)
        return res[:-1]

    @logger.logger
    def code_section_local(self, data: ByteReader) -> list[int]:
        """Code Sectionのローカル変数を読み込む"""

        # ローカル変数の数を読み込む
        count = data.read_leb128()
        assert self.logger.debug(f"local count: {count}")

        # ローカル変数のデータを読み込む
        local: list[int] = []
        for _ in range(count):
            local_count = data.read_leb128()
            local_type = data.read_byte()
            local.extend([local_type] * local_count)
            assert self.logger.debug(f"type: {local_type} * {local_count}")

        # 解析結果を返す
        return local

    @logger.logger
    def export_section(self, data: ByteReader) -> list[ExportSection]:
        """Export Sectionを読み込む"""

        # Export Sectionの数を読み込む
        export_count = data.read_leb128()
        assert self.logger.debug(f"export count: {export_count}")

        # Export Sectionのデータを読み込む
        res: list[ExportSection] = []
        for _ in range(export_count):
            field_len = data.read_leb128()
            field = data.read_bytes(field_len)
            kind = data.read_byte()
            index = data.read_leb128()
            section = ExportSection(field_name=field, kind=kind, index=index)
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res

    @logger.logger
    def data_section(self, data: ByteReader) -> list[DataSection]:
        """Data Sectionを読み込む"""

        # Data Sectionの数を読み込む
        data_count = data.read_leb128()
        assert self.logger.debug(f"data count: {data_count}")

        # Data Sectionのデータを読み込む
        res: list[DataSection] = []
        for _ in range(data_count):
            data_type = data.read_byte()
            if data_type == 0:
                active = ModeActive(table=0, offset=self.code_section_instructions(data))
                init = data.read_bytes(data.read_leb128())
                section = DataSection(init=init.data, active=active)
            elif data_type == 1:
                init = data.read_bytes(data.read_leb128())
                section = DataSection(init=init.data, active=None)
            else:
                raise Exception("invalid data_type")
            assert self.logger.debug(section)
            res.append(section)

        # 解析結果を返す
        return res
