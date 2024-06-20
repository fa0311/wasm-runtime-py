from abc import ABC, abstractmethod
from enum import Enum

from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64


class BlockType(Enum):
    START = 0
    END = 1
    ELSE = 2


class Metadata:
    @staticmethod
    def opcode(*args: int):
        def decorator(func):
            func.opcode = args
            return func

        return decorator

    @staticmethod
    def block(block: BlockType):
        def decorator(func):
            func.block = block
            return func

        return decorator


class CodeSectionSpec(ABC):
    """Code Sectionの仕様"""

    @abstractmethod
    @Metadata.opcode(0x41)
    def const_i32(self, value: I32):
        pass

    @abstractmethod
    @Metadata.opcode(0x42)
    def const_i64(self, value: I64):
        pass

    @abstractmethod
    @Metadata.opcode(0x43)
    def const_f32(self, value: F32):
        pass

    @abstractmethod
    @Metadata.opcode(0x44)
    def const_f64(self, value: F64):
        pass

    @abstractmethod
    @Metadata.opcode(0x20)
    def local_get(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x21)
    def local_set(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x22)
    def local_tee(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x6A, 0x7C, 0x92, 0xA0)
    def add(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6B, 0x7D, 0x93, 0xA1)
    def sub(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6C, 0x7E, 0x94, 0xA2)
    def mul(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6E, 0x80, 0x95, 0xA3)
    def div(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6D, 0x7F)
    def div_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x70, 0x82)
    def rem(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6F, 0x81)
    def rem_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x46, 0x51, 0x5B, 0x61)
    def eq(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x47, 0x52, 0x5C, 0x62)
    def ne(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x45, 0x50)
    def eqz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4A, 0x55)
    def gt_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4B, 0x56, 0x5E, 0x64)
    def gt_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4F, 0x5A, 0x60, 0x66)
    def ge(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4E, 0x59)
    def ge_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x48, 0x53)
    def lt_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x49, 0x54, 0x5D, 0x63)
    def lt_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4D, 0x58, 0x5F, 0x65)
    def le(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4C, 0x57)
    def le_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x67, 0x79)
    def clz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x68, 0x7A)
    def ctz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x69, 0x7B)
    def popcnt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x71, 0x83)
    def and_(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x72, 0x84)
    def or_(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x73, 0x85)
    def xor(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x74, 0x86)
    def shl(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x75, 0x87)
    def shr_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x76, 0x88)
    def shr_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x77, 0x89)
    def rotl(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x78, 0x8A)
    def rotr(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8B, 0x99)
    def abs(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8C, 0x9A)
    def neg(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8D, 0x9B)
    def ceil(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8E, 0x9C)
    def floor(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8F, 0x9D)
    def trunc(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x90, 0x9E)
    def nearest(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x96, 0xA4)
    def min(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x97, 0xA5)
    def max(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x91, 0x9F)
    def sqrt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x98, 0xA6)
    def copysign(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x04)
    @Metadata.block(BlockType.START)
    def if_(self, type: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x05)
    @Metadata.block(BlockType.ELSE)
    def else_(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x0D)
    def br_if(self, count: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x0C)
    def br(self, count: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x02)
    @Metadata.block(BlockType.START)
    def block(self, block_type: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x03)
    @Metadata.block(BlockType.START)
    def loop(self, block_type: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x0B)
    @Metadata.block(BlockType.END)
    def block_end(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x10)
    def call(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x1A)
    def drop(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x0F)
    def return_(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA7)
    def wrap_i64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAC)
    def i64_extend_i32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAD)
    def i64_extend_i32(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC0)
    def i32_extend8(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC1)
    def i32_extend16(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC2)
    def i64_extend8(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC3)
    def i64_extend16(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC4)
    def i64_extend32(self):
        pass
