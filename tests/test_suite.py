import glob
import json
import logging
import os
import pathlib
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.wasm.loader.loader import WasmLoader
from src.wasm.runtime.runtime import WasmRuntime
from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64


class TestSuite(unittest.TestCase):
    def setUp(self):
        if __debug__:
            self.__set_logger()
        np.seterr(all="ignore")
        if not os.path.exists(".cache"):
            self.__set_wasm2json()

    def tearDown(self):
        logging.shutdown()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __set_logger(self):
        handler = logging.FileHandler(
            "latest.log",
            mode="a",
            encoding="utf-8",
            delay=True,
        )
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(message)s",
            handlers=[handler],
        )

    def __set_wasm2json(self):
        filelist = glob.glob("testsuite/*.wast")
        for path in filelist:
            name = pathlib.Path(path).stem
            os.makedirs(f".cache/{name}", exist_ok=True)
            subprocess.run(
                [
                    "wast2json",
                    f"testsuite/{name}.wast",
                    "-o",
                    f".cache/{name}/{name}.json",
                ],
            )

    def __get_test_suite_data(self, name: str):
        path = pathlib.Path(f".cache/{name}/{name}.json")

        with open(path, "rb") as f:
            source = json.load(f)

        res: list[tuple[bytes, list[dict]]] = []
        for cmd in source["commands"]:
            if cmd["type"] == "module":
                with open(f".cache/{name}/{cmd['filename']}", "rb") as f:
                    wasm = f.read()
                    res.append((wasm, []))
            elif cmd["type"] == "assert_return":
                res[-1][1].append(cmd)

        return res

    def __test_file(self, name: str):
        case = self.__get_test_suite_data(name)
        for i in range(len(case)):
            self.__test_index(name, i)

    def __test_index(self, name: str, index: int):
        d, cmds = self.__get_test_suite_data(name)[index]
        data = WasmRuntime(WasmLoader(d).load())

        for case, cmd in enumerate(cmds):
            param = {"name": name, "index": f"{index:04d}", "case": f"{case:04d}"}
            self.__test_run(data, cmd, param)

    def __test_index_case(self, name: str, index: int, case: int):
        d, cmds = self.__get_test_suite_data(name)[index]
        data = WasmRuntime(WasmLoader(d).load())
        param = {"name": name, "index": f"{index:04d}", "case": f"{case:04d}"}
        self.__test_run(data, cmds[case], param)

    def __test_run(self, data: WasmRuntime, cmd: dict, param: dict[str, str]):
        with self.subTest(**param):
            field = bytes(cmd["action"]["field"], "utf-8")
            type_map = {
                "i32": lambda x: I32.from_str(x),
                "i64": lambda x: I64.from_str(x),
                "f32": lambda x: F32.from_str(x),
                "f64": lambda x: F64.from_str(x),
            }
            args = cmd["action"]["args"]
            expect = cmd["expected"]
            p: list[NumericType] = [type_map[value["type"]](value["value"]) for value in args]
            ee: list[NumericType] = [type_map[value["type"]](value["value"]) for value in expect]
            assert data is not None
            runtime = data.start(
                field=field,
                param=p,
            )
            res = runtime.run()
            for i, (r, e) in enumerate(zip(res, ee)):
                a, b = r.value, e.value
                if str(a) != str(b):
                    self.fail(f"expect: {b}, actual: {a}")

    def subTest(self, **param):
        SUBTEST = True
        if SUBTEST:
            return super().subTest(**param)
        else:
            return self

    def test_comments(self):
        self.__test_file("comments")

    def test_type(self):
        self.__test_file("type")

    def test_inline_module(self):
        self.__test_file("inline-module")

    def test_int_literals(self):
        self.__test_file("int_literals")

    def test_i32(self):
        self.__test_file("i32")

    def test_i64(self):
        self.__test_file("i64")

    def test_int_exprs(self):
        self.__test_file("int_exprs")

    def test_f32(self):
        self.__test_file("f32")

    def test_f32_bitwise(self):
        self.__test_file("f32_bitwise")

    def test_f32_cmp(self):
        self.__test_file("f32_cmp")

    def test_f64(self):
        self.__test_file("f64")

    def test_f64_bitwise(self):
        self.__test_file("f64_bitwise")

    def test_f64_cmp(self):
        self.__test_file("f64_cmp")

    def test_float_misc(self):
        self.__test_file("float_misc")

    def test_fac(self):
        self.__test_file("fac")

    def test_fac_0_3(self):
        self.__test_index_case("fac", 0, 4)


if __name__ == "__main__":
    unittest.main()
