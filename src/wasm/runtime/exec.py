import logging
from typing import Callable, Optional, TypeVar

from src.tools.logger import NestedLogger
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
    CodeSectionOptimize,
    TableSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)
from src.wasm.runtime.code_exec import CodeSectionBlock
from src.wasm.runtime.export import WasmExport, WasmExportFunction, WasmExportGlobal, WasmExportMemory, WasmExportTable
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.base import AnyType
from src.wasm.type.bytes.numpy.base import NumpyBytesType
from src.wasm.type.table.base import TableType


class WasmExec:
    """Code Sectionのデータ構造"""

    logger = NestedLogger(logging.getLogger(__name__))
    T = TypeVar("T")

    def __init__(self, sections: WasmSectionsOptimize, export: list[WasmExport] = []):
        self.sections = sections
        self.export = export
        self.init()

    def init(self):
        self.functions: list[Callable[[list[AnyType]], list[AnyType]]] = [
            (lambda x, self=self, i=i: self.run(i, x)) for i in range(len(self.sections.function_section))
        ]
        self.import_init()
        memory_size = self.sections.memory_section[0].limits_min if self.sections.memory_section else 0
        self.memory = NumpyBytesType.from_size(len(self.sections.memory_section) * 64 * 1024 * memory_size)
        # self.globals = [
        #     WasmOptimizer.get_any_type(x.type).from_int(self.run_data_int(x.init)) for x in self.sections.global_section
        # ]
        self.globals = []
        for g in self.sections.global_section:
            data = self.run_data_int(g.init)
            if data is None:
                self.globals.append(WasmOptimizer.get_any_type(g.type).from_null())
            else:
                self.globals.append(WasmOptimizer.get_any_type(g.type).from_int(data))

        self.tables = [
            TableType(WasmOptimizer.get_ref_type(x.element_type), x.limits_min, x.limits_max)
            for x in self.sections.table_section
        ]
        self.init_memory: list[NumpyBytesType] = []
        self.drop_elem = [False for _ in self.sections.element_section]

        for data_section in self.sections.data_section:
            if data_section.active is not None:
                offset = self.run_data_int(data_section.active.offset)
                assert isinstance(offset, int)
                self.memory.store(offset=offset, value=data_section.init)
            # elif data_section.active is None:
            self.init_memory.append(NumpyBytesType.from_str(data_section.init))
            # self.memory.store(offset=0, value=data_section.init)
        self.table_init()

        start = self.sections.start_section[0].index if self.sections.start_section else None
        if start is not None:
            self.functions[start]([])

    def import_init(self):
        for elem in self.sections.import_section[::-1]:
            name = elem.name.data.decode()
            namespace = elem.module.data.decode()
            data = [x for x in self.export if x.name == name and x.namespace == namespace][0].data

            if elem.kind == 0x00:
                assert isinstance(data, WasmExportFunction)
                code = CodeSectionOptimize(
                    data=[CodeInstructionOptimize(opcode=0x00, args=[], child=[], else_child=[])],
                    local=[],
                )
                self.sections.function_section.insert(0, data.function)
                self.sections.code_section.insert(0, code)
                self.functions.insert(0, data.call)
            elif elem.kind == 0x01:
                assert isinstance(data, WasmExportTable)
                self.sections.table_section.insert(0, data.table)
            elif elem.kind == 0x02:
                assert isinstance(data, WasmExportMemory)
                self.sections.memory_section.insert(0, data.memory)
            elif elem.kind == 0x03:
                assert isinstance(data, WasmExportGlobal)
                self.sections.global_section.insert(0, data.global_)
            else:
                raise Exception("not implemented import kind")

    def get_export(self, namespace: str) -> list[WasmExport]:
        res: list[WasmExport] = []

        for elem in self.sections.export_section:
            if elem.kind == 0x00:
                data = WasmExportFunction(
                    function=self.sections.function_section[elem.index],
                    # code=self.sections.code_section[elem.index],
                    call=self.functions[elem.index],
                )
            elif elem.kind == 0x01:
                data = WasmExportTable(
                    table=self.sections.table_section[elem.index],
                )
            elif elem.kind == 0x02:
                data = WasmExportMemory(
                    memory=self.sections.memory_section[elem.index],
                )
            elif elem.kind == 0x03:
                data = WasmExportGlobal(
                    global_=self.sections.global_section[elem.index],
                )
            else:
                raise Exception("not implemented export kind")

            res.append(WasmExport(namespace=namespace, name=elem.field_name.data.decode(), data=data))
        return res

    def table_init(self):
        for i, elem in enumerate(self.sections.element_section):
            if elem.active is not None:
                self.drop_elem[i] = True
                # se = self.sections.table_section[elem.active.table]
                # self.tables.append(TableType(WasmOptimizer.get_ref_type(se.element_type), se.limits_min, se.limits_max))
                for i, funcidx in enumerate(elem.funcidx or []):
                    table = self.sections.table_section[elem.active.table]
                    offset = self.run_data_int(elem.active.offset)
                    assert isinstance(offset, int)
                    ref = WasmOptimizer.get_ref_type(table.element_type)
                    self.tables[elem.active.table][offset + i] = ref.from_value(funcidx)

            # if elem.elem == 3:  # declarative
            #     self.drop_elem[i] = True

    @logger.logger
    def start(self, field: bytes, param: list[AnyType]):
        """エントリーポイントを実行する"""

        assert self.logger.info(f"field: {field.decode()}")

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.sections.export_section if fn.field_name == field][0]

        return self.functions[start.index](param)

    def run(self, index: int, param: list[AnyType]):
        fn, fn_type = self.get_function(index)

        # ローカル変数とExecインスタンスを生成
        locals_param = [WasmOptimizer.get_any_type(x).from_null() for x in fn.local]
        locals = [*param, *locals_param]
        block = self.get_block(locals=locals, stack=[])

        # 実行
        res = block.run(fn.data)
        if isinstance(res, list):
            returns = [res.pop() for _ in fn_type.returns][::-1]
        else:
            returns = [block.stack.any() for _ in fn_type.returns][::-1]
        assert self.logger.debug(f"res: {returns}")

        return returns

    def run_data_result(self, data: list[CodeInstructionOptimize]):
        block = self.get_block(locals=[], stack=[])
        res = block.run(data)
        if isinstance(res, list):
            returns = [res.pop() for _ in range(len(block.stack.value))]
        else:
            returns = [block.stack.any() for _ in range(len(block.stack.value))]
        assert self.logger.debug(f"res: {returns}")
        return returns

    def run_data_int(self, data: list[CodeInstructionOptimize]):
        returns = self.run_data_result(data)[0]
        return None if returns.is_none() else int(returns.value)

    def get_function(self, index: int) -> tuple[CodeSectionOptimize, TypeSectionOptimize]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        fn = self.sections.function_section[index]
        type = self.sections.type_section[fn.type]
        code = self.sections.code_section[index]
        return code, type

    def get_type(self, index: int) -> tuple[list[int], Optional[list[int]]]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""

        if index < len(self.sections.type_section):
            type = self.sections.type_section[index]
            return type.params, type.returns
        else:
            type = WasmOptimizer.get_type_or_none(index)
            returns = None if type is None else [type]
            return [], returns

    def get_table(self, index: int) -> tuple[TableSectionOptimize, TableType]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""
        return self.sections.table_section[index], self.tables[index]

    def get_block(self, locals: list[AnyType], stack: list[AnyType]):
        return CodeSectionBlock(
            env=self,
            locals=locals,
            stack=NumericStack(value=stack),
        )
