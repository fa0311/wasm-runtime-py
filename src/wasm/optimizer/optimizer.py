from typing import Optional

from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import BlockType
from src.wasm.loader.struct import (
    CodeInstruction,
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
from src.wasm.type.externref.base import ExternRef
from src.wasm.type.numeric.base import NumericType
from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I32, I64


class WasmOptimizer:
    def __init__(self, sections: "WasmSections"):
        self.sections = sections

    @staticmethod
    def get_type(type: int):
        if type == 0x7F:
            return I32
        if type == 0x7E:
            return I64
        if type == 0x7D:
            return F32
        if type == 0x7C:
            return F64
        if type == 0x40:
            return None
        if type == 0x6F:
            return ExternRef

        raise Exception(f"invalid type: {type:02X}")

    @staticmethod
    def get_type_or_none(type: int) -> Optional[int]:
        if type == 0x40:
            return None
        return type

    @staticmethod
    def get_numeric_type(type: int) -> type[NumericType]:
        if type == 0x7F:
            return I32
        if type == 0x7E:
            return I64
        if type == 0x7D:
            return F32
        if type == 0x7C:
            return F64

        raise Exception(f"invalid type: {type:02X}")

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
            type=section.type,
            table=section.table,
            data=self.expr(section.data),
            funcidx=section.funcidx,
        )

    def code_section(self, section: "CodeSection") -> "CodeSectionOptimize":
        res = CodeSectionOptimize(
            data=self.expr(section.data),
            local=section.local,
        )
        return res

    def expr(self, data: list[CodeInstruction]) -> list[CodeInstructionOptimize]:
        pointer = 0

        def child_fn():
            nonlocal pointer
            res: list[list[CodeInstructionOptimize]] = [[]]
            while len(data) > pointer:
                o = data[pointer]
                pointer += 1
                block_type = CodeSectionSpecHelper.get_block_type(o.opcode)
                if block_type == BlockType.START:
                    child = child_fn()
                    instruction = CodeInstructionOptimize(
                        opcode=o.opcode,
                        args=o.args,
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
                        opcode=o.opcode,
                        args=o.args,
                        child=[],
                        else_child=[],
                    )
                    res[-1].append(instruction)
            return res

        return child_fn()[0]

    def export_section(self, section: "ExportSection") -> "ExportSectionOptimize":
        return ExportSectionOptimize(
            field_name=section.field_name,
            kind=section.kind,
            index=section.index,
        )
