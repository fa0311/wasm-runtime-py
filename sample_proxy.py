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
        f"https://www.ipa.go.jp{path}{name}",
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        },
    )
    with urllib.request.urlopen(req) as res:
        body = res.read()
    try:
        body = body.decode().replace("セキュリティ", "インチキ").replace("デジタル", "インチキ").encode("utf-8")
    except UnicodeDecodeError:
        pass
    # with open(f"./files{name}", "wb") as f:
    #     f.write(body)

    return {"path": f"files{name}", "file": io.BytesIO(body)}


if __name__ == "__main__":
    with open("./assets/wasm_static_file_server/target/wasm32-wasi/release/static_file_server.wasm", "rb") as f:
        wasm = f.read()

    np.seterr(all="ignore")
    assert set_logger()

    data = WasmLoader().load(wasm)
    optimizer = WasmOptimizer().optimize(data)

    files = FS()

    files.mount(**proxy("/timetable.html", "/jinzai/security-camp/2024/camp/zenkoku/"))
    files.mount("files/favicon.ico", io.BytesIO(b""))
    files.mount(**proxy("/common/css/style.css"))
    files.mount(**proxy("/common/img/logo.svg"))
    files.mount(**proxy("/common/img/icon-fb.png"))
    files.mount(**proxy("/common/img/icon-tw.png"))
    files.mount(**proxy("/common/img/icon-yt.png"))
    files.mount(**proxy("/common/js/vender.js"))
    files.mount(**proxy("/jinzai/security-camp/2024/camp/zenkoku/m42obm0000005pyq-img/m42obm0000005q3w.png"))
    files.mount(**proxy("/common/img/icon-search_w.png"))
    files.mount(**proxy("/jinzai/security-camp/2024/camp/zenkoku/m42obm0000005pyq-img/m42obm0000005q4c.png"))
    files.mount(**proxy("/common/img/digital-hr/digital-hr_mv_pc.png"))
    files.mount(**proxy("/common/img/arw-down.png"))
    files.mount(**proxy("/common/js/common.js"))
    files.mount(**proxy("/common/img/icon-out.png"))
    files.mount(**proxy("/common/img/icon-send.png"))
    files.mount(**proxy("/icon-192x192.png"))
    files.mount(**proxy("/common/js/jvn.js"))
    files.mount(**proxy("/jinzai/security-camp/2024/camp/zenkoku/m42obm0000005pyq-img/m42obm0000005r4r.png"))
    files.mount(**proxy("/jinzai/security-camp/2024/camp/zenkoku/m42obm0000005pyq-img/m42obm0000005r51.png"))
    files.mount(**proxy("/jinzai/security-camp/2024/camp/zenkoku/m42obm0000005pyq-img/m42obm0000005r5b.png"))
    files.mount(**proxy("/jvn.rdf"))
    files.mount(**proxy("/k3q2q4000000ejg8-img/qv6pgp0000000s3p.png"))
    files.mount(**proxy("/k3q2q4000000ejg8-img/ps6vr7000000ih98.png"))
    files.mount(**proxy("/k3q2q4000000ejg8-img/ps6vr7000000iha0.png"))

    ins = Wasi()
    export = WasiExportHelperUtil.export(ins, "wasi_snapshot_preview1")

    dummy = WasiExportHelperUtil.dummy(optimizer)

    exec = WasmExec(optimizer, export + dummy)
    ins.init(exec=exec, fs=files)

    exec.start(b"_start", [])
