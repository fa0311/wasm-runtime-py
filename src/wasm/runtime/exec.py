import logging
from typing import Optional

from src.tools.logger import NestedLogger
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import (
    CodeSectionOptimize,
    ElementSectionOptimize,
    TableSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)
from src.wasm.runtime.code_exec import CodeSectionBlock
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.base import AnyType
from src.wasm.type.bytes.numpy.base import NumpyBytesType
from src.wasm.type.table.base import TableType


class WasmExec:
    """Code Sectionのデータ構造"""

    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(self, sections: WasmSectionsOptimize):
        self.sections = sections
        self.reset()

    def reset(self):
        memory_size = self.sections.memory_section[0].limits_min if self.sections.memory_section else 0
        self.memory = NumpyBytesType.from_size(len(self.sections.memory_section) * 64 * 1024 * memory_size)
        self.globals = [WasmOptimizer.get_any_type(x.type).from_null() for x in self.sections.global_section]
        self.tables = [
            TableType.from_size(WasmOptimizer.get_ref_type(x.element_type), x.limits_min)
            for x in self.sections.table_section
        ]

        for table_index, table in enumerate(self.sections.table_section):
            ref = WasmOptimizer.get_ref_type(table.element_type)
            element = self.get_table_elem(table_index)
            if  element is not None and element.active is not None:
                for funcidx in element.funcidx:
                    self.tables[table_index][element.active.offset] = ref.from_value(funcidx)
            elif element is not None:
                for funcidx in element.funcidx:
                    self.run(funcidx, [])

        for data_section in self.sections.data_section:
            self.memory.store(offset=data_section.offset, value=data_section.init)

    @logger.logger
    def start(self, field: bytes, param: list[AnyType]):
        """エントリーポイントを実行する"""

        assert self.logger.info(f"field: {field.decode()}")

        # エントリーポイントの関数を取得する
        start = [fn for fn in self.sections.export_section if fn.field_name == field][0]

        return self.run(start.index, param)

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

        return (block, returns)

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

    def get_table_elem(self, index: int) -> Optional[ElementSectionOptimize]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""
        element = [x for x in self.sections.element_section if x.active is not None and x.active.table == index]
        elem = element[0] if len(element) > 0 else None
        return elem

    def get_table(self, index: int) -> tuple[TableSectionOptimize, TableType]:
        """関数のインデックスからCode SectionとType Sectionを取得する"""
        return self.sections.table_section[index], self.tables[index]

    def get_block(self, locals: list[AnyType], stack: list[AnyType]):
        return CodeSectionBlock(
            env=self,
            locals=locals,
            stack=NumericStack(value=stack),
        )
