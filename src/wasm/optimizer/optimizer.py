from typing import Optional

from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import BlockType
from src.wasm.loader.struct import (
    CodeSection,
    ElementSection,
    ExportSection,
    FunctionSection,
    GlobalSection,
    MemorySection,
    TableSection,
    TypeSection,
    WasmSections,
)
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
    CodeSectionOptimize,
    ElementSectionOptimize,
    ExportSectionOptimize,
    FunctionSectionOptimize,
    GlobalSectionOptimize,
    MemorySectionOptimize,
    TableSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)
from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64


class WasmOptimizer:
    def __init__(self, sections: "WasmSections"):
        self.sections = sections

    @staticmethod
    def get_type(type: int) -> type[NumericType]:
        if type == 0x7F:
            return I32
        if type == 0x7E:
            return I64
        if type == 0x7D:
            return F32
        if type == 0x7C:
            return F64
        raise Exception(f"invalid type: {type:02X}")

    @staticmethod
    def get_type_or_none(type: int) -> Optional[int]:
        if type == 0x40:
            return None
        return type

    def optimize(self) -> "WasmSectionsOptimize":
        opt = WasmSectionsOptimize(
            type_section=[self.type_section(x) for x in self.sections.type_section],
            function_section=[self.function_section(x) for x in self.sections.function_section],
            table_section=[self.table_section(x) for x in self.sections.table_section],
            memory_section=[self.memory_section(x) for x in self.sections.memory_section],
            global_section=[self.global_section(x) for x in self.sections.global_section],
            element_section=[self.element_section(x) for x in self.sections.element_section],
            code_section=[self.code_section(x) for x in self.sections.code_section],
            export_section=[self.export_section(x) for x in self.sections.export_section],
        )
        return opt

    def type_section(self, section: "TypeSection") -> "TypeSectionOptimize":
        return TypeSectionOptimize(
            form=section.form,
            params=section.params,
            returns=section.returns,
        )

    def function_section(self, section: "FunctionSection") -> "FunctionSectionOptimize":
        return FunctionSectionOptimize(
            type=section.type,
        )

    def table_section(self, section: "TableSection") -> "TableSectionOptimize":
        return TableSectionOptimize(
            element_type=section.element_type,
            limits=section.limits,
        )

    def memory_section(self, section: "MemorySection") -> "MemorySectionOptimize":
        return MemorySectionOptimize(
            limits=section.limits,
        )

    def global_section(self, section: "GlobalSection") -> "GlobalSectionOptimize":
        return GlobalSectionOptimize(
            type=section.type,
            mutable=section.mutable,
            init=section.init,
        )

    def element_section(self, section: "ElementSection") -> "ElementSectionOptimize":
        return ElementSectionOptimize(
            table=section.table,
            type=section.type,
            init=section.init,
        )

    def code_section(self, section: "CodeSection") -> "CodeSectionOptimize":
        pointer = 0

        def child_fn():
            nonlocal pointer
            res: list[list[CodeInstructionOptimize]] = [[]]
            while True:
                data = section.data[pointer]
                pointer += 1
                block_type = CodeSectionSpecHelper.get_block_type(data.opcode)
                if block_type == BlockType.START:
                    child = child_fn()
                    instruction = CodeInstructionOptimize(
                        opcode=data.opcode,
                        args=data.args,
                        child=child[0],
                        else_child=child[1] if len(child) > 1 else [],
                    )
                    res[-1].append(instruction)
                elif block_type == BlockType.END:
                    return res
                elif block_type == BlockType.ELSE:
                    res.append([])
                else:
                    instruction = CodeInstructionOptimize(
                        opcode=data.opcode,
                        args=data.args,
                        child=[],
                        else_child=[],
                    )
                    res[-1].append(instruction)

        child = child_fn()
        res = CodeSectionOptimize(
            data=child[0],
            local=section.local,
        )
        return res

    def export_section(self, section: "ExportSection") -> "ExportSectionOptimize":
        return ExportSectionOptimize(
            field_name=section.field_name,
            kind=section.kind,
            index=section.index,
        )
