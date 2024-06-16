from abc import ABC, abstractmethod
from typing import Callable

from src.wasm.type.main import F32, F64, LEB128


def metadata(*args: int):
    def decorator(func):
        func.metadata = args
        return func

    return decorator


class CodeSectionSpec(ABC):
    """Code Sectionの仕様"""

    @abstractmethod
    @metadata(0x41, 0x42)
    def i32_const(self, value: LEB128):
        pass

    @abstractmethod
    @metadata(0x43)
    def push_f32(self, value: F32):
        pass

    @abstractmethod
    @metadata(0x44)
    def push_f64(self, value: F64):
        pass

    @abstractmethod
    @metadata(0x20)
    def local_get(self, index: int):
        pass

    @abstractmethod
    @metadata(0x21)
    def local_set(self, index: int):
        pass

    @abstractmethod
    @metadata(0x22)
    def local_tee(self, index: int):
        pass

    @abstractmethod
    @metadata(0x6A, 0x7C, 0x92, 0xA0)
    def add(self):
        pass

    @abstractmethod
    @metadata(0x6B, 0x7D, 0x93, 0xA1)
    def sub(self):
        pass

    @abstractmethod
    @metadata(0x6C, 0x7E, 0x94, 0xA2)
    def mul(self):
        pass

    @abstractmethod
    @metadata(0x6E, 0x7F, 0x80, 0x95, 0xA3)
    def div(self):
        pass

    @abstractmethod
    @metadata(0x6D)
    def div_s(self):
        pass

    @abstractmethod
    @metadata(0x70, 0x81, 0x82)
    def rem(self):
        pass

    @abstractmethod
    @metadata(0x6F)
    def rem_s(self):
        pass

    @abstractmethod
    @metadata(0x46, 0x51, 0x5B, 0x61)
    def eq(self):
        pass

    @abstractmethod
    @metadata(0x47, 0x52, 0x5C, 0x62)
    def ne(self):
        pass

    @abstractmethod
    @metadata(0x45, 0x50)
    def eqz(self):
        pass

    @abstractmethod
    @metadata(0x4A)
    def gt_s(self):
        pass

    @abstractmethod
    @metadata(0x4B, 0x55, 0x56, 0x5E, 0x64)
    def gt_u(self):
        pass

    @abstractmethod
    @metadata(0x4E, 0x4F, 0x59, 0x5A, 0x60, 0x66)
    def ge(self):
        pass

    @abstractmethod
    @metadata(0x48)
    def lt_s(self):
        pass

    @abstractmethod
    @metadata(0x49, 0x53, 0x54, 0x5D, 0x63)
    def lt_u(self):
        pass

    @abstractmethod
    @metadata(0x4C, 0x4D, 0x57, 0x58, 0x5F, 0x65)
    def le(self):
        pass

    @abstractmethod
    @metadata(0x67)
    def i32_clz(self):
        pass

    @abstractmethod
    @metadata(0x68)
    def i32_ctz(self):
        pass

    @abstractmethod
    @metadata(0x69)
    def i32_popcnt(self):
        pass

    @abstractmethod
    @metadata(0x71, 0x83)
    def and_(self):
        pass

    @abstractmethod
    @metadata(0x72, 0x84)
    def or_(self):
        pass

    @abstractmethod
    @metadata(0x73, 0x85)
    def xor(self):
        pass

    @abstractmethod
    @metadata(0x74)
    def i32_shl(self):
        pass

    @abstractmethod
    @metadata(0x75)
    def i32_shr_s(self):
        pass

    @abstractmethod
    @metadata(0x76)
    def i32_shr_u(self):
        pass

    @abstractmethod
    @metadata(0x77)
    def i32_rotl(self):
        pass

    @abstractmethod
    @metadata(0x78)
    def i32_rotr(self):
        pass

    @abstractmethod
    @metadata(0x04)
    def if_(self, type: int):
        pass

    @abstractmethod
    @metadata(0x05)
    def else_(self):
        pass

    @abstractmethod
    @metadata(0x0D)
    def br_if(self, count: int):
        pass

    @abstractmethod
    @metadata(0x0C)
    def br(self, count: int):
        pass

    @abstractmethod
    @metadata(0x02)
    def block(self, block_type: int):
        pass

    @abstractmethod
    @metadata(0x03)
    def loop(self, block_type: int):
        pass

    @abstractmethod
    @metadata(0x0B)
    def block_end(self):
        pass

    @abstractmethod
    @metadata(0x10)
    def call(self, index: int):
        pass

    @abstractmethod
    @metadata(0x1A)
    def drop(self):
        pass

    @abstractmethod
    @metadata(0x0F)
    def return_(self):
        pass

    def error(self):
        raise Exception("naver calle")

    @classmethod
    def mapped(cls, opcode: int) -> Callable:
        value = CodeSectionSpec.__dict__.values()
        data = {}
        for v in value:
            if hasattr(v, "metadata"):
                for m in v.metadata:
                    data[m] = v

        return data.get(opcode, cls.error)

    @classmethod
    def bind(cls, pearent: "CodeSectionSpec", opcode: int):
        name = pearent.mapped(opcode).__name__
        if name == "error":
            raise Exception(f"opcode: {opcode:02X} is not defined")
        return getattr(pearent, name)
