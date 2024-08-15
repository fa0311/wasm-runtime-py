import io
import logging
import os
import urllib.request

import numpy as np

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import FS, Wasi, WasiExportHelperUtil


def set_logger():
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
    return True


def proxy(name: str, path: str = ""):
    req = urllib.request.Request(
        f"https://silentspacemarine.com/{path}{name}",
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req) as res:
        body = res.read()

    if name == "":
        return {"path": "files/index.html", "file": io.BytesIO(body)}
    else:
        return {"path": f"files{name}", "file": io.BytesIO(body)}


if __name__ == "__main__":
    with open("./assets/wasm_static_file_server/target/wasm32-wasi/release/static_file_server.wasm", "rb") as f:
        wasm = f.read()

    np.seterr(all="ignore")
    assert set_logger()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    files = FS()
    files.mount("files/favicon.ico", io.BytesIO(b""))
    files.mount(**proxy(""))
    files.mount(**proxy("/romero.css"))
    files.mount(**proxy("/hidetoolbar.png"))
    files.mount(**proxy("/carmack.js"))
    files.mount(**proxy("/romero.js"))
    files.mount(**proxy("/websockets-doom.js"))
    files.mount(**proxy("/retro.png"))
    files.mount(**proxy("/websockets-doom.wasm"))
    files.mount(**proxy("/doom1.wad"))
    files.mount(**proxy("/default.cfg"))

    ins = Wasi()
    export = WasiExportHelperUtil.export(ins, "wasi_snapshot_preview1")

    dummy = WasiExportHelperUtil.dummy(optimizer)

    exec = WasmExec(optimizer, export + dummy)
    ins.init(exec=exec, fs=files)

    exec.start(b"_start", [])
