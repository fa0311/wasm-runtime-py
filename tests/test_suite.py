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
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec, WasmUnimplementedError
from src.wasm.type.base import NumericType
from src.wasm.type.numpy.float import F32, F64
from src.wasm.type.numpy.int import I32, I64


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.__set_logger()
        if not os.path.exists(".cache"):
            self.__set_wasm2json()

    def tearDown(self):
        logging.shutdown()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def __set_logger(self):
        if __debug__:
            filename = "latest.log"
            if os.path.exists(filename):
                os.remove(filename)
            handler = logging.FileHandler(
                filename,
                mode="a",
                encoding="utf-8",
                delay=True,
            )
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(message)s",
                handlers=[handler],
            )
        else:
            np.seterr(all="ignore")
            logging.basicConfig(level=logging.FATAL)

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
        wasm, cmds = self.__get_test_suite_data(name)[index]
        data = WasmLoader(wasm).load()
        optimizer = WasmOptimizer(data).optimize()
        data = WasmExec(optimizer)

        for case, cmd in enumerate(cmds):
            param = {"name": name, "index": f"{index:04d}", "case": f"{case:04d}"}
            with self.subTest(**param):
                self.__test_run(data, cmd)

    def __test_index_case(self, name: str, index: int, case: int):
        wasm, cmds = self.__get_test_suite_data(name)[index]
        data = WasmLoader(wasm).load()
        optimizer = WasmOptimizer(data).optimize()
        data = WasmExec(optimizer)
        self.__test_run(data, cmds[case])

    def __test_run(self, data: WasmExec, cmd: dict):
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
        try:
            runtime, res = data.start(
                field=field,
                param=p,
            )
            for i, (r, e) in enumerate(zip(res, ee)):
                a, b = r.value, e.value
                if str(a) != str(b):
                    self.fail(f"expect: {b}, actual: {a}")
        except WasmUnimplementedError as e:
            self.skipTest(str(e))

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

    # def test_conversions(self):
    #     self.__test_file("conversions")

    # def test_float_literals(self):
    #     self.__test_file("float_literals")

    def test_forward(self):
        self.__test_file("forward")

    def test_const(self):
        self.__test_file("const")

    def test_local_get(self):
        self.__test_file("local_get")

    # def test_local_set(self):
    #     self.__test_file("local_set")

    # def test_labels(self):
    #     self.__test_file("labels")

    # def test_switch(self):
    #     self.__test_file("switch")

    # def test_store(self):
    #     self.__test_file("store")

    # def test_block(self):
    #     self.__test_file("block")

    # def test_br(self):
    #     self.__test_file("br")

    # def test_br_0_70(self):
    #     self.__test_index_case("br", 0, 70)

    # def test_br_0_73(self):
    #     self.__test_index_case("br", 0, 73)

    # def test_br_0_75(self):
    #     self.__test_index_case("br", 0, 75)

    # def test_br_if(self):
    #     self.__test_file("br_if")

    # def test_br_table(self):
    #     self.__test_file("br_table")

    # def test_return(self):
    #     self.__test_file("return")

    # def test_call_indirect(self):
    #     self.__test_file("call_indirect")

    # def test_call(self):
    #     self.__test_file("call")


if __name__ == "__main__":
    unittest.main()
