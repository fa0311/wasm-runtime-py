import io
import logging
import os
import sys
import time
from typing import Callable

import numpy as np
import pygame

from src.tools.logger import NestedLogger
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import CodeSectionOptimize, TypeSectionOptimize, WasmSectionsOptimize
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.export import WasmExport, WasmExportFunction
from src.wasm.type.base import AnyType
from src.wasm.type.numeric.base import NumericType
from src.wasm.type.numeric.numpy.int import I32, I64

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "true"


class WasiResult:
    SUCCESS = (I32.from_int(0),)
    BADF = (I32.from_int(8),)
    INVAL = (I32.from_int(28),)
    NOENT = (I32.from_int(44),)


class FileType:
    DIR = 3
    REG = 4


class WasiExportHelperUtil:
    logger = NestedLogger(logging.getLogger(__name__))

    @classmethod
    def export(cls, clss: type, namespace: str) -> list[WasmExport]:
        value = clss.__dict__.values()
        ins = clss()
        data: list[WasmExport] = []
        for v in value:
            if isinstance(v, Callable):
                ignore = ["env", "return"]
                annotations: list[type[NumericType]] = [v for k, v in v.__annotations__.items() if k not in ignore]
                ret = [v for k, v in v.__annotations__.items() if k == "return"]

                returns: list[type[NumericType]] = ret[0].__args__ if ret else []

                def call(env: WasmExec, args: list[AnyType], ins=ins, name=v.__name__, annotations=annotations):
                    if name != "fd_write":
                        WasiExportHelperUtil.logger.debug(f"call: {name}")
                    args_int = [
                        x if issubclass(annotations[i], NumericType) else annotations[i](x) for i, x in enumerate(args)
                    ]
                    return getattr(ins, name)(env, *args_int) or []

                data.append(
                    WasmExport(
                        namespace=namespace,
                        name=v.__name__,
                        data=WasmExportFunction(
                            type=TypeSectionOptimize(
                                form=0,
                                params=[
                                    WasmOptimizer.from_type(x if issubclass(x, NumericType) else I32)
                                    for x in annotations
                                ],
                                returns=[
                                    WasmOptimizer.from_type(x if issubclass(x, NumericType) else I32) for x in returns
                                ],
                            ),
                            code=CodeSectionOptimize(data=[], local=[]),
                            call=call,
                        ),
                    )
                )

        return data

    @classmethod
    def dummy(cls, opt: WasmSectionsOptimize) -> list[WasmExport]:
        data: list[WasmExport] = []
        for a in opt.import_section:
            data.append(
                WasmExport(
                    namespace=a.module.data.decode(),
                    name=a.name.data.decode(),
                    data=WasmExportFunction(
                        type=TypeSectionOptimize(form=0, params=[], returns=[]),
                        code=CodeSectionOptimize(data=[], local=[]),
                        call=lambda env, x: [],
                    ),
                )
            )
        return data


WAD = "mount/doom1.wad"
f_doom = open(WAD, "rb")
f_scr = io.BytesIO()
f_pal = io.BytesIO()


img_size = (320, 200)
(img_w, img_h) = img_size
scr_size = (img_w * 2, img_h * 2)
pygame.init()
surface = pygame.display.set_mode(scr_size)
pygame.display.set_caption("DOOM")
clock = pygame.time.Clock()


def update_screen():
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    if len(f_pal.getbuffer()) != 3 * 256 or len(f_scr.getbuffer()) != 320 * 200:
        return

    scr = np.frombuffer(f_scr.getbuffer(), dtype=np.uint8)
    pal = np.frombuffer(f_pal.getbuffer(), dtype=np.uint8).reshape((256, 3))

    # Convert indexed color to RGB
    arr = pal[scr]

    data = arr.astype(np.uint8).tobytes()

    img = pygame.image.frombuffer(data, img_size, "RGB")

    img_scaled = pygame.transform.scale(img, scr_size)
    surface.blit(img_scaled, (0, 0))
    pygame.display.flip()

    clock.tick(60)


def stdout_write(data):
    sys.stdout.buffer.write(data)


vfs = {
    "<stdin>": {"fd": 0, "type": FileType.REG, "write": stdout_write},
    "<stdout>": {"fd": 1, "type": FileType.REG, "write": stdout_write},
    "<stderr>": {"fd": 2, "type": FileType.REG, "write": stdout_write},
    "/": {"fd": 3, "type": FileType.DIR, "dirname": b"/\x00"},
    "./doom1.wad": {"fd": 5, "type": FileType.REG, "file": f_doom, "exists": True},
    "./screen.data": {"fd": 6, "type": FileType.REG, "file": f_scr, "exists": False},
    "./palette.raw": {"fd": 7, "type": FileType.REG, "file": f_pal, "exists": False},
}
vfs_fds = {v["fd"]: v for (k, v) in vfs.items()}


class Wasi:
    def args_sizes_get(self, env: WasmExec, argc: int, buf_szv: int) -> tuple[I32]:
        env.memory[argc : argc + 4] = I32.from_int(3).to_bytes()[0:4]
        env.memory[buf_szv : buf_szv + 4] = I32.from_int(32).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def args_get(self, env: WasmExec, argv: int, buf: I32) -> tuple[I32]:
        env.memory[argv : argv + 4] = buf.to_bytes()[0:4]
        env.memory.store(int(buf), b"doom\0")

        return WasiResult.SUCCESS

    def environ_sizes_get(self, env: WasmExec, envc: int, buf_sz: int) -> tuple[I32]:
        env.memory[envc : envc + 4] = I32.from_int(1).to_bytes()[0:4]
        env.memory[buf_sz : buf_sz + 4] = I32.from_int(32).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def environ_get(self, env: WasmExec, a: int, b: I32) -> tuple[I32]:
        env.memory[a : a + 4] = b.to_bytes()[0:4]
        env.memory.store(int(b), b"HOME=/\0")
        return WasiResult.SUCCESS

    def fd_prestat_get(self, env: WasmExec, envs: int, buf: int) -> tuple[I32]:
        if envs != 3:
            return WasiResult.BADF

        name_len = len(vfs_fds[envs]["dirname"])
        env.memory[buf : buf + 4] = I32.from_int(0).to_bytes()[0:4]
        env.memory[buf + 4 : buf + 8] = I32.from_int(name_len).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def fd_fdstat_get(self, env: WasmExec, fd: int, result: int):
        if fd >= len(vfs_fds):
            return WasiResult.BADF

        f = vfs_fds[fd]
        env.memory[result : result + 1] = I32.from_int(f["type"]).to_bytes()[0:1]
        env.memory[result + 1 : result + 2] = I32.from_int(0).to_bytes()[0:1]
        env.memory[result + 2 : result + 10] = I64.from_int(I64.get_max()).to_bytes()[0:8]
        env.memory[result + 10 : result + 18] = I64.from_int(I64.get_max()).to_bytes()[0:8]

        return WasiResult.SUCCESS

    def fd_prestat_dir_name(self, env: WasmExec, fd: int, name: int, name_len: int) -> tuple[I32]:
        path = vfs_fds[fd]["dirname"]
        env.memory.store(name, path)
        return WasiResult.SUCCESS

    def path_filestat_get(self, env: WasmExec, fd: int, flags: int, path: int, path_len: int, buff: int) -> tuple[I32]:
        path_str = env.memory[path : path + path_len].tobytes().decode()
        if path_str not in vfs or not vfs[path_str]["exists"]:
            return WasiResult.BADF

        f = vfs[path_str]
        if "size" in f:
            size = f["size"]
        elif "file" in f:
            fh = f["file"]
            cur = fh.tell()
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(cur, 0)

        env.memory[buff : buff + 8] = I64.from_int(1).to_bytes()[0:8]
        env.memory[buff + 8 : buff + 16] = I64.from_int(1).to_bytes()[0:8]
        env.memory[buff + 16 : buff + 17] = I32.from_int(f["type"]).to_bytes()[0:1]
        env.memory[buff + 17 : buff + 24] = I64.from_int(1).to_bytes()[0:7]
        env.memory[buff + 24 : buff + 32] = I64.from_int(size).to_bytes()[0:8]
        env.memory[buff + 32 : buff + 40] = I64.from_int(0).to_bytes()[0:8]
        env.memory[buff + 40 : buff + 48] = I64.from_int(0).to_bytes()[0:8]
        env.memory[buff + 48 : buff + 56] = I64.from_int(0).to_bytes()[0:8]

        return WasiResult.SUCCESS

    def path_open(
        self,
        env: WasmExec,
        dirfd: int,
        dirflags: int,
        path: int,
        path_len: int,
        oflags: int,
        fs_rights_base: int,
        fs_rights_inheriting: int,
        fs_flags: int,
        fd: int,
    ) -> tuple[I32]:
        path_name = env.memory[path : path + path_len].tobytes().decode()
        if path_name not in vfs:
            return WasiResult.NOENT
        else:
            f = vfs[path_name]
            f["exists"] = True
            fd_val = f["fd"]
            env.memory[fd : fd + 4] = I32.from_int(fd_val).to_bytes()[0:4]

            return WasiResult.SUCCESS

    def fd_seek(self, env: WasmExec, fd: int, offset: int, whence: int, result: int) -> tuple[I32]:
        if fd not in vfs_fds:
            return WasiResult.BADF

        if "file" not in vfs_fds[fd]:
            return WasiResult.INVAL

        f = vfs_fds[fd]["file"]
        f.seek(offset, whence)
        res = f.tell()
        env.memory[result : result + 8] = I64.from_int(res).to_bytes()[0:8]
        return WasiResult.SUCCESS

    def fd_close(self, env: WasmExec, a: I32):
        return WasiResult.SUCCESS

    def fd_read(self, env: WasmExec, fd: int, iovs: int, iovs_len: int, nread: int):
        data_sz = 0
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(env.memory[iov : iov + 4])
            size = I32.from_bits(env.memory[iov + 4 : iov + 8])
            data_sz += int(size)

        data = None
        if fd in vfs_fds:
            if "read" in vfs_fds[fd]:
                data = vfs_fds[fd]["read"](data_sz)
            elif "file" in vfs_fds[fd]:
                data = vfs_fds[fd]["file"].read(data_sz)

        if not data:
            return WasiResult.BADF

        data_off = 0
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(env.memory[iov : iov + 4])
            size = I32.from_bits(env.memory[iov + 4 : iov + 8])
            d = data[data_off : data_off + int(size)]
            env.memory.store(int(off), d)
            data_off += len(d)

        env.memory[nread : nread + 4] = I32.from_int(data_off).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def fd_write(self, env: WasmExec, fd: int, iovs: int, iovs_len: int, nwritten: int) -> tuple[I32]:
        data = b""
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(env.memory[iov : iov + 4])
            size = I32.from_bits(env.memory[iov + 4 : iov + 8])
            data += env.memory[int(off) : int(off) + int(size)].tobytes()

        if fd not in vfs_fds:
            return WasiResult.BADF

        if "write" in vfs_fds[fd]:
            vfs_fds[fd]["write"](data)
        elif "file" in vfs_fds[fd]:
            vfs_fds[fd]["file"].write(data)
            update_screen()

        env.memory[nwritten : nwritten + 4] = I32.from_int(len(data)).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def clock_time_get(self, env: WasmExec, clk_id: int, precision: int, result: int) -> tuple[I32]:
        t = int(time.time_ns())
        env.memory[result : result + 8] = I64.from_int(t).to_bytes()[0:8]
        return WasiResult.SUCCESS

    def proc_exit(self, env: WasmExec, a: int):
        sys.exit(a)

    def fd_filestat_get(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")

    def poll_oneoff(self, env: WasmExec, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def path_create_directory(self, env: WasmExec, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def fd_fdstat_set_flags(self, env: WasmExec, a: I32, b: I32):
        raise Exception("not implemented")
