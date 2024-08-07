import logging
from typing import TYPE_CHECKING, Optional, Union

from src.tools.logger import NestedLogger
from src.wasm.loader.helper import CodeSectionSpecHelper
from src.wasm.loader.spec import CodeSectionSpec
from src.wasm.optimizer.struct import (
    CodeInstructionOptimize,
)
from src.wasm.runtime.stack import NumericStack
from src.wasm.type.base import AnyType

if TYPE_CHECKING:
    from src.wasm.runtime.exec import WasmExec


class CodeSectionRun(CodeSectionSpec):
    logger = NestedLogger(logging.getLogger(__name__))

    def __init__(
        self,
        env: "WasmExec",
        locals: list[AnyType],
        stack: NumericStack,
    ):
        self.env = env
        self.locals = locals

        self.stack = stack
        self.instruction: CodeInstructionOptimize

    @logger.logger
    def run(self, code: list[CodeInstructionOptimize]) -> Optional[Union[int, list[AnyType]]]:
        assert self.logger.debug(f"params: {self.stack.value}")
        for data in code:
            res = self.run_instruction(data)
            if res is not None:
                return res

    def run_instruction(self, data: CodeInstructionOptimize):
        self.instruction = data
        opcode = self.instruction.opcode
        args = self.instruction.args
        assert self.logger.debug(f"run: {self.instruction}")
        fn = CodeSectionSpecHelper.bind(self, opcode)
        return fn(*args)
