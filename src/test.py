import glob
import json
import logging
import pathlib
import sys

from tools.formatter import ColorFormatter
from wasm.loader import WasmLoader
from wasm.runtime import WasmRuntime

if __name__ == "__main__":
    # ログの設定
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter())
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        handlers=[handler],
    )

    # 引数を解析してWasmバイナリを読み込む
    args = sys.argv
    file = "*" if len(args) < 2 else args[1]

    filelist = glob.glob(f".cache/{file}/*.json")
    for path in filelist:
        name = pathlib.Path(path).stem
        print(path)

        with open(path, "rb") as f:
            source = json.load(f)

        data: list = []
        for cmd in source["commands"]:
            if cmd["type"] == "module":
                # Wasmバイナリを読み込む
                with open(f".cache/{name}/{cmd['filename']}", "rb") as f:
                    wasm = f.read()
                data = WasmLoader(wasm).load()
            elif cmd["type"] == "assert_return":
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
