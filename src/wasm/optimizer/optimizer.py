from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import BlockType, CodeSectionSpec
from src.wasm.loader.struct import (
    CodeSection,
    ExportSection,
    FunctionSection,
    TypeSection,
    WasmSections,
)
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
    CodeSectionOptimize,
    ExportSectionOptimize,
    FunctionSectionOptimize,
    TypeSectionOptimize,
    WasmSectionsOptimize,
)


class WasmOptimizer:
    def __init__(self, sections: "WasmSections"):
        self.sections = sections

    def optimize(self) -> "WasmSectionsOptimize":
        opt = WasmSectionsOptimize(
            type_section=[self.type_section(x) for x in self.sections.type_section],
            function_section=[self.function_section(x) for x in self.sections.function_section],
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

    def code_section(self, section: "CodeSection") -> "CodeSectionOptimize":
        block_start_stack: list[int] = []
        block_end_stack: list[int] = []
        start_res: list[list[int]] = []
        end_res: list[list[int]] = []
        res: list[CodeInstructionOptimize] = []

        block_start_stack.append(-1)

        for index, data in enumerate(section.data):
            block_type = CodeSectionSpecHelper.get_block_type(data.opcode)
            start_res.append(block_start_stack.copy())
            if block_type == BlockType.START:
                block_start_stack.append(index)
            elif block_type == BlockType.END:
                block_start_stack.pop()
            elif block_type == BlockType.ELSE:
                block_start_stack.pop()
                block_start_stack.append(index)

        length = len(section.data)
        for index, data in enumerate(section.data[::-1]):
            block_type = CodeSectionSpecHelper.get_block_type(data.opcode)
            end_res.append(block_end_stack.copy())
            if block_type == BlockType.START:
                block_end_stack.pop()
            elif block_type == BlockType.END:
                block_end_stack.append(length - index - 1)
            elif block_type == BlockType.ELSE:
                block_end_stack.pop()
                block_end_stack.append(length - index - 1)

        for index, data in enumerate(section.data):
            parent = section.data[start_res[index][-1]]
            res.append(
                CodeInstructionOptimize(
                    opcode=data.opcode,
                    args=data.args,
                    loop=parent.opcode == CodeSectionSpec.loop.opcode[0],
                    block_start=start_res[index],
                    block_end=end_res[-(index + 1)],
                )
            )

        return CodeSectionOptimize(
            data=res,
            local=section.local,
        )

    def export_section(self, section: "ExportSection") -> "ExportSectionOptimize":
        return ExportSectionOptimize(
            field_name=section.field_name,
            kind=section.kind,
            index=section.index,
        )
