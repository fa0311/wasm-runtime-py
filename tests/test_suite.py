import glob
import json
import logging
import os
import pathlib
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.tools.formatter import ColorFormatter
from src.wasm.loader import WasmLoader
from src.wasm.runtime import WasmRuntime


class TestSuite(unittest.TestCase):
    test_suite_data: dict[str, tuple[list, list[dict]]] = {}

    def setUp(self):
        if not os.path.exists(".cache"):
            self.__set_wasm2json()
        if not self.test_suite_data:
            self.__set_test_suite_data()

        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter())
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

    def __set_test_suite_data(self):
        filelist = glob.glob(".cache/*/*.json")
        for path in filelist:
            name = pathlib.Path(path).stem

            with open(path, "rb") as f:
                source = json.load(f)

            for cmd in source["commands"]:
                if cmd["type"] == "module":
                    with open(f".cache/{name}/{cmd['filename']}", "rb") as f:
                        wasm = f.read()
                    self.test_suite_data[name] = (WasmLoader(wasm).load(), [])
                elif cmd["type"] == "assert_return":
                    self.test_suite_data[name][1].append(cmd)

    def __test_file(self, name: str):
        case = self.test_suite_data[name]
        for i in range(len(case[1])):
            self.__test_case(name, i)

    def __test_case(self, name: str, index: int):
        cmd = self.test_suite_data[name][1][index]
        data = self.test_suite_data[name][0]

        with self.subTest(name=name, case=index):
            field = bytes(cmd["action"]["field"], "utf-8")
            param = cmd["action"]["args"]
            type_map = {
                "i32": int,
                "i64": int,
                "f32": float,
                "f64": float,
            }
            res = WasmRuntime(data).start(
                field=field,
                param=[type_map[value["type"]](value["value"]) for value in param],
            )
            expect = cmd["expected"]
            for i, (r, e) in enumerate(zip(res, expect)):
                if r != type_map[e["type"]](e["value"]):
                    raise AssertionError(
                        f"assert_return failed: {r} != {e['value']} at {i}"
                    )

    @unittest.skip("skip")
    def test_all(self):
        for name in self.test_suite_data:
            self.__test_file(name)

    def test_i32(self):
        self.__test_file("i32")


if __name__ == "__main__":
    unittest.main()
