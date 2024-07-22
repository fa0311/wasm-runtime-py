from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable

from src.wasm.type.numeric.numpy.float import F32, F64
from src.wasm.type.numeric.numpy.int import I32, I64


class BlockType(Enum):
    START = 0
    END = 1
    ELSE = 2


class Metadata:
    @staticmethod
    def opcode(*args: int):
        def decorator(func: Callable):
            func.opcode = args
            return func

        return decorator

    @staticmethod
    def block(block: BlockType):
        def decorator(func: Callable):
            func.block = block
            return func

        return decorator


class CodeSectionSpec(ABC):
    """Code Sectionの仕様"""

    # Control Instructions

    @abstractmethod
    @Metadata.opcode(0x00)
    def unreachable(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x01)
    def nop(self):
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
    @Metadata.opcode(0x0B)
    @Metadata.block(BlockType.END)
    def block_end(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x0C)
    def br(self, count: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x0D)
    def br_if(self, count: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x0E)
    def br_table(self, count: list[int]):
        pass

    @abstractmethod
    @Metadata.opcode(0x0F)
    def return_(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x10)
    def call(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x11)
    def call_indirect(self, index: int, elm_index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x1A)
    def drop(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x1B)
    def select(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x1C)
    def select_t(self, _: int, type: int):
        pass

    # Variable Instructions

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
    @Metadata.opcode(0x23)
    def global_get(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x24)
    def global_set(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x25)
    def table_get(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x26)
    def table_set(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x28)
    def i32_load(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x29)
    def i64_load(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x2A)
    def f32_load(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x2B)
    def f64_load(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x2C)
    def i32_load8_s(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x2D)
    def i32_load8_u(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x2E)
    def i32_load16_s(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x2F)
    def i32_load16_u(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x30)
    def i64_load8_s(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x31)
    def i64_load8_u(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x32)
    def i64_load16_s(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x33)
    def i64_load16_u(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x34)
    def i64_load32_s(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x35)
    def i64_load32_u(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x36)
    def i32_store(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x37)
    def i64_store(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x38)
    def f32_store(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x39)
    def f64_store(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x3A)
    def i32_store8(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x3B)
    def i32_store16(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x3C)
    def i64_store8(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x3D)
    def i64_store16(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x3E)
    def i64_store32(self, align: int, offset: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x3F)
    def memory_size(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x40)
    def memory_grow(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0x41)
    def i32_const(self, value: I32):
        pass

    @abstractmethod
    @Metadata.opcode(0x42)
    def i64_const(self, value: I64):
        pass

    @abstractmethod
    @Metadata.opcode(0x43)
    def f32_const(self, value: F32):
        pass

    @abstractmethod
    @Metadata.opcode(0x44)
    def f64_const(self, value: F64):
        pass

    @abstractmethod
    @Metadata.opcode(0x45)
    def i32_eqz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x46)
    def i32_eq(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x47)
    def i32_ne(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x48)
    def i32_lt_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x49)
    def i32_lt_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4A)
    def i32_gt_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4B)
    def i32_gt_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4C)
    def i32_le_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4D)
    def i32_le_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4E)
    def i32_ge_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x4F)
    def i32_ge_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x50)
    def i64_eqz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x51)
    def i64_eq(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x52)
    def i64_ne(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x53)
    def i64_lt_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x54)
    def i64_lt_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x55)
    def i64_gt_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x56)
    def i64_gt_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x57)
    def i64_le_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x58)
    def i64_le_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x59)
    def i64_ge_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x5A)
    def i64_ge_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x5B)
    def f32_eq(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x5C)
    def f32_ne(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x5D)
    def f32_lt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x5E)
    def f32_gt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x5F)
    def f32_le(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x60)
    def f32_ge(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x61)
    def f64_eq(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x62)
    def f64_ne(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x63)
    def f64_lt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x64)
    def f64_gt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x65)
    def f64_le(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x66)
    def f64_ge(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x67)
    def i32_clz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x68)
    def i32_ctz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x69)
    def i32_popcnt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6A)
    def i32_add(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6B)
    def i32_sub(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6C)
    def i32_mul(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6D)
    def i32_div_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6E)
    def i32_div_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x6F)
    def i32_rem_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x70)
    def i32_rem_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x71)
    def i32_and(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x72)
    def i32_or(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x73)
    def i32_xor(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x74)
    def i32_shl(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x75)
    def i32_shr_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x76)
    def i32_shr_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x77)
    def i32_rotl(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x78)
    def i32_rotr(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x79)
    def i64_clz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x7A)
    def i64_ctz(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x7B)
    def i64_popcnt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x7C)
    def i64_add(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x7D)
    def i64_sub(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x7E)
    def i64_mul(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x7F)
    def i64_div_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x80)
    def i64_div_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x81)
    def i64_rem_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x82)
    def i64_rem_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x83)
    def i64_and(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x84)
    def i64_or(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x85)
    def i64_xor(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x86)
    def i64_shl(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x87)
    def i64_shr_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x88)
    def i64_shr_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x89)
    def i64_rotl(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8A)
    def i64_rotr(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8B)
    def f32_abs(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8C)
    def f32_neg(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8D)
    def f32_ceil(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8E)
    def f32_floor(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x8F)
    def f32_trunc(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x90)
    def f32_nearest(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x91)
    def f32_sqrt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x92)
    def f32_add(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x93)
    def f32_sub(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x94)
    def f32_mul(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x95)
    def f32_div(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x96)
    def f32_min(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x97)
    def f32_max(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x98)
    def f32_copysign(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x99)
    def f64_abs(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x9A)
    def f64_neg(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x9B)
    def f64_ceil(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x9C)
    def f64_floor(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x9D)
    def f64_trunc(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x9E)
    def f64_nearest(self):
        pass

    @abstractmethod
    @Metadata.opcode(0x9F)
    def f64_sqrt(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA0)
    def f64_add(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA1)
    def f64_sub(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA2)
    def f64_mul(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA3)
    def f64_div(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA4)
    def f64_min(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA5)
    def f64_max(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA6)
    def f64_copysign(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA7)
    def i32_wrap_i64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA8)
    def i32_trunc_f32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xA9)
    def i32_trunc_f32_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAA)
    def i32_trunc_f64_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAB)
    def i32_trunc_f64_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAC)
    def i64_extend_i32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAD)
    def i64_extend_i32_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAE)
    def i64_trunc_f32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xAF)
    def i64_trunc_f32_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB0)
    def i64_trunc_f64_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB1)
    def i64_trunc_f64_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB2)
    def f32_convert_i32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB3)
    def f32_convert_i32_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB4)
    def f32_convert_i64_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB5)
    def f32_convert_i64_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB6)
    def f32_demote_f64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB7)
    def f64_convert_i32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB8)
    def f64_convert_i32_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xB9)
    def f64_convert_i64_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xBA)
    def f64_convert_i64_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xBB)
    def f64_promote_f32(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xBC)
    def i32_reinterpret_f32(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xBD)
    def i64_reinterpret_f64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xBE)
    def f32_reinterpret_i32(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xBF)
    def f64_reinterpret_i64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC0)
    def i32_extend8_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC1)
    def i32_extend16_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC2)
    def i64_extend8_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC3)
    def i64_extend16_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xC4)
    def i64_extend32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xD0)
    def ref_null(self, type: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xD1)
    def ref_is_null(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xD2)
    def ref_func(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xD3)
    def ref_as_non_null(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC00)
    def i32_trunc_sat_f32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC01)
    def i32_trunc_sat_f32_u(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC02)
    def i32_trunc_sat_f64_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC03)
    def i32_trunc_sat_f64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC04)
    def i64_trunc_sat_f32_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC05)
    def i64_trunc_sat_f32(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC06)
    def i64_trunc_sat_f64_s(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC07)
    def i64_trunc_sat_f64(self):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC08)
    def memory_init(self, index: int, index2: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC09)
    def data_drop(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC0A)
    def memory_copy(self, index: int, index2: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC0B)
    def memory_fill(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC0C)
    def table_init(self, index: int, index2: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC0D)
    def elem_drop(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC0E)
    def table_copy(self, index: int, index2: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC0F)
    def table_grow(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC10)
    def table_size(self, index: int):
        pass

    @abstractmethod
    @Metadata.opcode(0xFC11)
    def table_fill(self, index: int):
        pass
