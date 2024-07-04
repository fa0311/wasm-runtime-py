import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.type.numeric.numpy.float import F64
from src.wasm.type.numeric.numpy.int import I32, SignedI32


class TestUnit(unittest.TestCase):
    def test_i32_div_floor(self):
        a = I32.from_int(7)
        b = I32.from_int(3)
        self.assertEqual((a / b).value, 2)

    def test_signed_i32_mod(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(3)
        self.assertEqual((a % b).value, -1)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a % b).value, 1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a % b).value, -1)

    def test_signed_i32_div_floor(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(3)
        self.assertEqual((a / b).value, -2)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a / b).value, -2)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a / b).value, 2)

    def test_signed_i32_div_ceil(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(4)
        self.assertEqual((a / b).value, -1)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-4)
        self.assertEqual((a / b).value, -1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-4)
        self.assertEqual((a / b).value, 1)

    def test_signed_i64_mod(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(3)
        self.assertEqual((a % b).value, -1)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a % b).value, 1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a % b).value, -1)

    def test_signed_i64_div_floor(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(3)
        self.assertEqual((a / b).value, -2)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a / b).value, -2)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-3)
        self.assertEqual((a / b).value, 2)

    def test_signed_i64_div_ceil(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(4)
        self.assertEqual((a / b).value, -1)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-4)
        self.assertEqual((a / b).value, -1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-4)
        self.assertEqual((a / b).value, 1)

    def test_float_zero_min_max(self):
        a = F64(np.float64(0.0))
        b = F64(np.float64(-0.0))
        self.assertEqual(str(a.min(b).value), str(b.value))
        self.assertEqual(str(a.max(b).value), str(a.value))
        self.assertEqual(str(b.min(a).value), str(b.value))
        self.assertEqual(str(b.max(a).value), str(a.value))

    def test_float_sqrt(self):
        a = F64(np.float64(-0.0))
        self.assertEqual(str(a.sqrt().value), str(a.value))
