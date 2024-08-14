import logging
import os

from src.wasm.loader.loader import WasmLoader
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.wasi import FS, Screen, WasiExportHelperUtil


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


if __name__ == "__main__":
    with open("assets/wasidoom2.wasm", "rb") as f:
        wasm = f.read()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    screen = Screen()

    f_doom = open("./assets/doom1.wad", "rb")

    files = FS()
    files.mount("./doom1.wad", f_doom, fd=5, exists=True)
    files.mount("./screen.data", screen.f_scr, fd=6, exists=False)
    files.mount("./palette.raw", screen.f_pal, fd=7, exists=False)

    ins, export = WasiExportHelperUtil.export("wasi_snapshot_preview1")
    dummy = WasiExportHelperUtil.dummy(optimizer)

    exec = WasmExec(optimizer, export + dummy)

    ins.init(exec=exec, fs=files, screen=screen, environ={"HOME": "/"})

    assert set_logger()
    exec.start(b"_start", [])
    # exec.start(b"main", [])
