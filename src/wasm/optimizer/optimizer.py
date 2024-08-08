from typing import Optional

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
    StartSection,
    TableSection,
    TypeSection,
    WasmSections,
)
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
    CodeSectionOptimize,
    DataSectionOptimize,
    ElementSectionOptimize,
    ExportSectionOptimize,
    FunctionSectionOptimize,
    GlobalSectionOptimize,
    ImportSectionOptimize,
    MemorySectionOptimize,
    ModeActiveOptimize,
    StartSectionOptimize,
    TableSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)
from src.wasm.type.base import AnyType
from src.wasm.type.numeric.base import NumericType
from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I32, I64
from src.wasm.type.ref.base import ExternRef, FuncRef, RefType


class WasmOptimizer:
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
        if type == 0x70:
            return FuncRef

        raise Exception(f"invalid type: {type:02X}")

    @staticmethod
    def from_type(type: type[NumericType]):
        if type is I32:
            return 0x7F
        if type is I64:
            return 0x7E
        if type is F32:
            return 0x7D
        if type is F64:
            return 0x7C
        raise Exception(f"invalid type: {type}")

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

    @staticmethod
    def get_any_type(type: int) -> type[AnyType]:
        if type == 0x7F:
            return I32
        if type == 0x7E:
            return I64
        if type == 0x7D:
            return F32
        if type == 0x7C:
            return F64
        if type == 0x6F:
            return ExternRef
        if type == 0x70:
            return FuncRef
        raise Exception(f"invalid type: {type:02X}")

    @staticmethod
    def get_ref_type(type: int) -> type[RefType]:
        if type == 0x6F:
            return ExternRef
        if type == 0x70:
            return FuncRef
        raise Exception(f"invalid type: {type:02X}")

    def optimize(self, sections: "WasmSections") -> "WasmSectionsOptimize":
        opt = WasmSectionsOptimize(
            import_section=[self.import_section(x) for x in sections.import_section],
            type_section=[self.type_section(x) for x in sections.type_section],
            function_section=[self.function_section(x) for x in sections.function_section],
            table_section=[self.table_section(x) for x in sections.table_section],
            memory_section=[self.memory_section(x) for x in sections.memory_section],
            start_section=[self.start_section(x) for x in sections.start_section],
            global_section=[self.global_section(x) for x in sections.global_section],
            element_section=[self.element_section(x) for x in sections.element_section],
            code_section=[self.code_section(x) for x in sections.code_section],
            export_section=[self.export_section(x) for x in sections.export_section],
            data_section=[self.data_section(x) for x in sections.data_section],
        )
        return opt

    def import_section(self, section: "ImportSection") -> "ImportSectionOptimize":
        return ImportSectionOptimize(
            module=section.module,
            name=section.name,
            kind=section.kind,
        )

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
            limits_min=section.limits_min,
            limits_max=section.limits_max,
        )

    def memory_section(self, section: "MemorySection") -> "MemorySectionOptimize":
        return MemorySectionOptimize(
            limits_min=section.limits_min,
            limits_max=section.limits_max,
        )

    def start_section(self, section: "StartSection") -> "StartSectionOptimize":
        return StartSectionOptimize(
            index=section.index,
        )

    def global_section(self, section: "GlobalSection") -> "GlobalSectionOptimize":
        return GlobalSectionOptimize(
            type=section.type,
            mutable=section.mutable,
            init=self.expr(section.init),
        )

    def element_section(self, section: "ElementSection") -> "ElementSectionOptimize":
        return ElementSectionOptimize(
            elem=section.elem,
            type=section.type,
            ref=self.expr(section.ref) if section.ref is not None else None,
            funcidx=section.funcidx,
            active=self.mode_active(section.active) if section.active is not None else None,
        )

    def mode_active(self, section: "ModeActive") -> "ModeActiveOptimize":
        return ModeActiveOptimize(
            table=section.table,
            offset=self.expr(section.offset),
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

    def data_section(self, section: "DataSection") -> "DataSectionOptimize":
        return DataSectionOptimize(
            active=self.mode_active(section.active) if section.active is not None else None,
            init=section.init,
        )
