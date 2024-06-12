import logging
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
    with open(args[1], "rb") as f:
        wasm = f.read()

    # Wasmバイナリを読み込んで実行する
    data = WasmLoader(wasm).load()
    WasmRuntime(data)
