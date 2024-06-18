import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.type.main import I32, SignedI32


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

    def test_signed_i32_div_cell(self):
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

    def test_signed_i64_div_cell(self):
        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(4)
        self.assertEqual((a / b).value, -1)

        a = SignedI32.from_int(7)
        b = SignedI32.from_int(-4)
        self.assertEqual((a / b).value, -1)

        a = SignedI32.from_int(-7)
        b = SignedI32.from_int(-4)
        self.assertEqual((a / b).value, 1)
