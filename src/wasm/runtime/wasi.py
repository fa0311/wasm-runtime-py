import io
import logging
import os
import random
import socket
import sys
import time
from typing import Callable, Optional

import numpy as np
import pygame

from src.tools.logger import NestedLogger
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import CodeSectionOptimize, TypeSectionOptimize, WasmSectionsOptimize
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.export import WasmExport, WasmExportFunction
from src.wasm.type.base import AnyType
from src.wasm.type.numeric.base import NumericType
from src.wasm.type.numeric.numpy.int import I8, I32, I64


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
    def export(cls, namespace: str) -> tuple["Wasi", list[WasmExport]]:
        value = Wasi.__dict__.values()
        ins = Wasi()
        data: list[WasmExport] = []
        for v in value:
            if isinstance(v, Callable) and v.__name__ != "init":
                ignore = ["return"]
                annotations: list[type[NumericType]] = [v for k, v in v.__annotations__.items() if k not in ignore]
                ret = [v for k, v in v.__annotations__.items() if k == "return"]

                returns: list[type[NumericType]] = ret[0].__args__ if ret else []

                def call(args: list[AnyType], ins=ins, name=v.__name__, annotations=annotations):
                    if name != "fd_write":
                        WasiExportHelperUtil.logger.debug(f"call: {name}")
                    args_int = [
                        x if issubclass(annotations[i], NumericType) else annotations[i](x) for i, x in enumerate(args)
                    ]
                    return getattr(ins, name)(*args_int) or []

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

        return (ins, data)

    @classmethod
    def dummy(cls, opt: WasmSectionsOptimize) -> list[WasmExport]:
        data: list[WasmExport] = []
        for a in opt.import_section:
            name = f"{a.module.data.decode()}::{a.name.data.decode()}"
            data.append(
                WasmExport(
                    namespace=a.module.data.decode(),
                    name=a.name.data.decode(),
                    data=WasmExportFunction(
                        type=TypeSectionOptimize(form=0, params=[], returns=[]),
                        code=CodeSectionOptimize(data=[], local=[]),
                        call=lambda x, name=name: cls.unreachable(name),
                    ),
                )
            )
        return data

    @classmethod
    def unreachable(cls, name: str):
        raise Exception("not implemented wasi function: " + name)


class Screen:
    def __init__(self) -> None:
        os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "true"
        self.img_size = (320, 200)

        self.f_scr = io.BytesIO()
        self.f_pal = io.BytesIO()

        (img_w, img_h) = self.img_size
        self.scr_size = (img_w * 2, img_h * 2)
        pygame.init()
        self.surface = pygame.display.set_mode(self.scr_size)
        pygame.display.set_caption("DOOM")
        self.clock = pygame.time.Clock()

    def update_screen(self):
        for event in pygame.event.get():
            quit_key = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            if event.type == pygame.QUIT or quit_key:
                pygame.quit()
                sys.exit()

        if len(self.f_pal.getbuffer()) != 3 * 256 or len(self.f_scr.getbuffer()) != 320 * 200:
            return

        scr = np.frombuffer(self.f_scr.getbuffer(), dtype=np.uint8)
        pal = np.frombuffer(self.f_pal.getbuffer(), dtype=np.uint8).reshape((256, 3))

        # Convert indexed color to RGB
        arr = pal[scr]

        data = arr.astype(np.uint8).tobytes()

        img = pygame.image.frombuffer(data, self.img_size, "RGB")

        img_scaled = pygame.transform.scale(img, self.scr_size)
        self.surface.blit(img_scaled, (0, 0))
        pygame.display.flip()

        self.clock.tick(60)


def stdout_write(data):
    sys.stdout.write(data.decode())
    sys.stdout.flush()


class FS:
    def __init__(self) -> None:
        self.files = {
            "<stdin>": {"fd": 0, "type": FileType.REG, "write": stdout_write},
            "<stdout>": {"fd": 1, "type": FileType.REG, "write": stdout_write},
            "<stderr>": {"fd": 2, "type": FileType.REG, "write": stdout_write},
            "/": {"fd": 3, "type": FileType.DIR, "dirname": b"/\x00"},
        }

    def mount(self, path: str, fd: int, file: io.BufferedIOBase, exists: bool = True):
        self.files[path] = {"fd": fd, "type": FileType.REG, "file": file, "exists": exists}

    @property
    def fds(self):
        return {v["fd"]: v for (k, v) in self.files.items()}


class Wasi:
    fs: FS
    env: WasmExec
    screen: Optional[Screen]

    def init(self, env: WasmExec, fs: Optional[FS] = None, screen: Optional[Screen] = None):
        self.env = env
        self.fs = fs or FS()
        if screen:
            self.screen = screen

    def args_sizes_get(self, argc: int, buf_szv: int) -> tuple[I32]:
        self.env.memory[argc : argc + 4] = I32.from_int(3).to_bytes()[0:4]
        self.env.memory[buf_szv : buf_szv + 4] = I32.from_int(32).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def args_get(self, argv: int, buf: I32) -> tuple[I32]:
        self.env.memory[argv : argv + 4] = buf.to_bytes()[0:4]
        self.env.memory.store(int(buf), b"doom\0")

        return WasiResult.SUCCESS

    def environ_sizes_get(self, envc: int, buf_sz: int) -> tuple[I32]:
        self.env.memory[envc : envc + 4] = I32.from_int(1).to_bytes()[0:4]
        self.env.memory[buf_sz : buf_sz + 4] = I32.from_int(32).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def environ_get(self, a: int, b: I32) -> tuple[I32]:
        self.env.memory[a : a + 4] = b.to_bytes()[0:4]

        aa = {
            "HOME": b"",
            "PATH": b"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        }
        self.env.memory.store(int(b), "\0".join([f"{k}={v}" for k, v in aa.items()]).encode())
        return WasiResult.SUCCESS

    def fd_prestat_get(self, envs: int, buf: int) -> tuple[I32]:
        if envs != 3:
            return WasiResult.BADF

        name_len = len(self.fs.fds[envs]["dirname"])
        self.env.memory[buf : buf + 4] = I32.from_int(0).to_bytes()[0:4]
        self.env.memory[buf + 4 : buf + 8] = I32.from_int(name_len).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def fd_fdstat_get(self, fd: int, result: int):
        if fd >= len(self.fs.fds):
            return WasiResult.BADF

        f = self.fs.fds[fd]
        self.env.memory[result : result + 1] = I32.from_int(f["type"]).to_bytes()[0:1]
        self.env.memory[result + 1 : result + 2] = I32.from_int(0).to_bytes()[0:1]
        self.env.memory[result + 2 : result + 10] = I64.from_int(I64.get_max()).to_bytes()[0:8]
        self.env.memory[result + 10 : result + 18] = I64.from_int(I64.get_max()).to_bytes()[0:8]

        return WasiResult.SUCCESS

    def fd_prestat_dir_name(self, fd: int, name: int, name_len: int) -> tuple[I32]:
        path = self.fs.fds[fd]["dirname"]
        self.env.memory.store(name, path)
        return WasiResult.SUCCESS

    def path_filestat_get(self, fd: int, flags: int, path: int, path_len: int, buff: int) -> tuple[I32]:
        path_str = self.env.memory[path : path + path_len].tobytes().decode()
        if path_str not in self.fs.files or not self.fs.files[path_str]["exists"]:
            return WasiResult.BADF

        f = self.fs.files[path_str]
        if "size" in f:
            size = f["size"]
        elif "file" in f:
            fh = f["file"]
            cur = fh.tell()
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(cur, 0)

        self.env.memory[buff : buff + 8] = I64.from_int(1).to_bytes()[0:8]
        self.env.memory[buff + 8 : buff + 16] = I64.from_int(1).to_bytes()[0:8]
        self.env.memory[buff + 16 : buff + 17] = I32.from_int(f["type"]).to_bytes()[0:1]
        self.env.memory[buff + 17 : buff + 24] = I64.from_int(1).to_bytes()[0:7]
        self.env.memory[buff + 24 : buff + 32] = I64.from_int(size).to_bytes()[0:8]
        self.env.memory[buff + 32 : buff + 40] = I64.from_int(0).to_bytes()[0:8]
        self.env.memory[buff + 40 : buff + 48] = I64.from_int(0).to_bytes()[0:8]
        self.env.memory[buff + 48 : buff + 56] = I64.from_int(0).to_bytes()[0:8]

        return WasiResult.SUCCESS

    def path_open(
        self,
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
        path_name = self.env.memory[path : path + path_len].tobytes().decode()
        if path_name not in self.fs.files:
            return WasiResult.NOENT
        else:
            f = self.fs.files[path_name]
            f["exists"] = True
            fd_val = f["fd"]
            self.env.memory[fd : fd + 4] = I32.from_int(fd_val).to_bytes()[0:4]

            return WasiResult.SUCCESS

    def fd_seek(self, fd: int, offset: int, whence: int, result: int) -> tuple[I32]:
        if fd not in self.fs.fds:
            return WasiResult.BADF

        if "file" not in self.fs.fds[fd]:
            return WasiResult.INVAL

        f = self.fs.fds[fd]["file"]
        f.seek(offset, whence)
        res = f.tell()
        self.env.memory[result : result + 8] = I64.from_int(res).to_bytes()[0:8]
        return WasiResult.SUCCESS

    def fd_close(self, a: I32):
        return WasiResult.SUCCESS

    def fd_read(self, fd: int, iovs: int, iovs_len: int, nread: int):
        data_sz = 0
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(self.env.memory[iov : iov + 4])
            size = I32.from_bits(self.env.memory[iov + 4 : iov + 8])
            data_sz += int(size)

        data = None
        if fd in self.fs.fds:
            if "read" in self.fs.fds[fd]:
                data = self.fs.fds[fd]["read"](data_sz)
            elif "file" in self.fs.fds[fd]:
                data = self.fs.fds[fd]["file"].read(data_sz)

        if not data:
            return WasiResult.BADF

        data_off = 0
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(self.env.memory[iov : iov + 4])
            size = I32.from_bits(self.env.memory[iov + 4 : iov + 8])
            d = data[data_off : data_off + int(size)]
            self.env.memory.store(int(off), d)
            data_off += len(d)

        self.env.memory[nread : nread + 4] = I32.from_int(data_off).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def fd_write(self, fd: int, iovs: int, iovs_len: int, nwritten: int) -> tuple[I32]:
        data = b""
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(self.env.memory[iov : iov + 4])
            size = I32.from_bits(self.env.memory[iov + 4 : iov + 8])
            data += self.env.memory[int(off) : int(off) + int(size)].tobytes()

        if fd not in self.fs.fds:
            return WasiResult.BADF

        if "write" in self.fs.fds[fd]:
            self.fs.fds[fd]["write"](data)
        elif "file" in self.fs.fds[fd]:
            self.fs.fds[fd]["file"].write(data)
            if self.screen:
                self.screen.update_screen()

        self.env.memory[nwritten : nwritten + 4] = I32.from_int(len(data)).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def clock_time_get(self, clk_id: int, precision: int, result: int) -> tuple[I32]:
        t = int(time.time_ns())
        self.env.memory[result : result + 8] = I64.from_int(t).to_bytes()[0:8]
        return WasiResult.SUCCESS

    def proc_exit(self, a: int):
        sys.exit(a)

    def fd_filestat_get(self, a: I32, b: I32):
        raise Exception("not implemented")

    def poll_oneoff(self, a: I32, b: I32, c: I32):
        return WasiResult.NOENT

    def path_create_directory(self, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def fd_fdstat_set_flags(self, a: I32, b: I32):
        raise Exception("not implemented")

    def random_get(self, a: I32, b: int):
        rand = random.randint(0, 2**32 - 1)
        self.env.memory[b : b + 4] = I32.from_int(rand).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def sock_open(self, family: int, sock_type: int, fd: int) -> tuple[I32]:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        return WasiResult.SUCCESS

        self.socket = socket.socket(family, sock_type)
        res = self.socket.fileno()

        self.env.memory[fd : fd + 4] = I32.from_int(res).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def sock_setsockopt(
        self,
        fd: int,
        level: int,
        name: int,
        flag_ptr: int,
        flag_size: int,
    ) -> tuple[I32]:
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return WasiResult.SUCCESS
        flag = I8.from_bits(self.env.memory[flag_ptr : flag_ptr + flag_size])

        self.socket.setsockopt(level, name, int(flag))

        return WasiResult.SUCCESS

    def sock_bind(self, fd: int, addr: int, port: int) -> tuple[I32]:
        off = I32.from_bits(self.env.memory[addr : addr + 4])
        size = I32.from_bits(self.env.memory[addr + 4 : addr + 8])

        addr_str = self.env.memory[int(off) : int(off) + int(size)].tobytes()
        addr_str = ".".join([str(x) for x in addr_str])
        self.socket.bind((addr_str, port))

        return WasiResult.SUCCESS

    def sock_listen(self, fd: int, backlog: int) -> tuple[I32]:
        self.socket.listen(backlog)
        return WasiResult.SUCCESS

    def sock_shutdown(self, fd: int, how: int) -> tuple[I32]:
        self.socket.shutdown(how)
        return WasiResult.SUCCESS
