import logging
import sys

from tools.formatter import ColorFormatter

from src.wasm.loader.loader import WasmLoader
from src.wasm.runtime.runtime import WasmRuntime

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
    with open(args[1], "rb") as f:
        wasm = f.read()

    # Wasmバイナリを読み込んで実行する
    data = WasmLoader(wasm).load()
    runner = WasmRuntime(data).start(field=b"_start", param=[])
    res = runner.run()
    logging.info(f"result: {res}")
