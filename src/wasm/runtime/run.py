import logging
from typing import TYPE_CHECKING, Optional, Union

from src.tools.logger import NestedLogger
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import CodeSectionSpec
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
)
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.base import NumericType

if TYPE_CHECKING:
    from src.wasm.runtime.exec import WasmExec


class CodeSectionRun(CodeSectionSpec):
    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(
        self,
        env: "WasmExec",
        code: list[CodeInstructionOptimize],
        locals: list[NumericType],
        stack: NumericStack,
    ):
        self.env = env
        self.locals = locals
        self.code = code

        self.stack = stack
        self.pointer = 0
        self.instruction: CodeInstructionOptimize

    @logger.logger
    def run(self) -> Optional[Union[int, list[NumericType]]]:
        self.logger.debug(f"params: {self.stack.value}")
        while self.pointer < len(self.code):
            res = self.run_instruction()
            if res is not None:
                return res

    def run_instruction(self):
        self.instruction = self.code[self.pointer]
        opcode = self.instruction.opcode
        args = self.instruction.args
        self.logger.debug(f"run: {self.instruction}")
        fn = CodeSectionSpecHelper.bind(self, opcode)
        self.pointer += 1
        return fn(*args)
