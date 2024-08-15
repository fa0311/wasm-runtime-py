import io
import logging
import random
import socket as sk
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np

from src.tools.logger import NestedLogger
from src.wasm.optimizer.optimizer import WasmOptimizer
from src.wasm.optimizer.struct import CodeSectionOptimize, TypeSectionOptimize, WasmSectionsOptimize
from src.wasm.runtime.exec import WasmExec
from src.wasm.runtime.export import WasmExport, WasmExportFunction
from src.wasm.runtime.screen.screen import Screen
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
    def export(cls, ins: "WasiBase", namespace: str) -> list[WasmExport]:
        value = ins.__class__.__dict__.values()
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

        return data

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


def stdout_write(data: bytes):
    sys.stdout.write(data.decode())
    sys.stdout.flush()


@dataclass
class FSModel:
    fd: int
    type: int
    exists: bool
    write: Optional[Callable[[bytes], None]] = None
    buffer: Optional[io.BufferedIOBase] = None
    dirname: Optional[str] = None
    sock: Optional[sk.socket] = None


class FS:
    files: dict[str, FSModel]

    def __init__(self) -> None:
        self.files = {
            "<stdin>": FSModel(fd=0, type=FileType.REG, write=stdout_write, exists=False),
            "<stdout>": FSModel(fd=1, type=FileType.REG, write=stdout_write, exists=False),
            "<stderr>": FSModel(fd=2, type=FileType.REG, write=stdout_write, exists=False),
            "/": FSModel(fd=3, type=FileType.DIR, write=stdout_write, dirname="/", exists=False),
        }

    def next_fd(self):
        return len(self.files) + 1

    def mount(self, path: str, file: io.BufferedIOBase, fd: Optional[int] = None, exists: bool = True):
        new_fd = fd or self.next_fd()
        self.files[path] = FSModel(fd=new_fd, type=FileType.REG, buffer=file, exists=exists)

    def add(self, name: str, n: FSModel):
        self.files[name] = n

    @property
    def fds(self):
        return {v.fd: v for (k, v) in self.files.items()}


class WasiBase:
    env: WasmExec

    def init(self, exec: WasmExec):
        self.exec = exec


class Wasi(WasiBase):
    fs: FS
    screen: Optional[Screen]
    environ: dict[str, str]

    def init(
        self,
        exec: WasmExec,
        fs: Optional[FS] = None,
        screen: Optional[Screen] = None,
        environ: Optional[dict[str, str]] = None,
    ):
        self.exec = exec
        self.fs = fs or FS()
        self.screen = screen
        self.environ = environ or {}
        if screen:
            self.screen = screen

    def args_sizes_get(self, argc: int, buf_szv: int) -> tuple[I32]:
        self.exec.memory[argc : argc + 4] = I32.from_int(3).to_bytes()[0:4]
        self.exec.memory[buf_szv : buf_szv + 4] = I32.from_int(32).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def args_get(self, argv: int, buf: I32) -> tuple[I32]:
        self.exec.memory[argv : argv + 4] = buf.to_bytes()[0:4]
        self.exec.memory.store(int(buf), b"doom\0")

        return WasiResult.SUCCESS

    def environ_sizes_get(self, envc: int, buf_sz: int) -> tuple[I32]:
        self.exec.memory[envc : envc + 4] = I32.from_int(len(self.environ)).to_bytes()[0:4]
        self.exec.memory[buf_sz : buf_sz + 4] = I32.from_int(32).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def environ_get(self, a: int, b: I32) -> tuple[I32]:
        self.exec.memory[a : a + 4] = b.to_bytes()[0:4]

        self.exec.memory.store(int(b), "\0".join([f"{k}={v}" for k, v in self.environ.items()]).encode())
        return WasiResult.SUCCESS

    def fd_prestat_get(self, fd: int, buf: int) -> tuple[I32]:
        if fd != 3:
            return WasiResult.BADF

        assert self.fs.fds[fd].dirname
        name_len = len(self.fs.fds[fd].dirname or "")
        self.exec.memory[buf : buf + 4] = I32.from_int(0).to_bytes()[0:4]
        self.exec.memory[buf + 4 : buf + 8] = I32.from_int(name_len).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def fd_fdstat_get(self, fd: int, result: int):
        if fd not in self.fs.fds:
            return WasiResult.BADF

        f = self.fs.fds[fd]
        self.exec.memory[result : result + 1] = I32.from_int(f.type).to_bytes()[0:1]
        self.exec.memory[result + 1 : result + 2] = I32.from_int(0).to_bytes()[0:1]
        self.exec.memory[result + 2 : result + 10] = I64.from_int(I64.get_max()).to_bytes()[0:8]
        self.exec.memory[result + 10 : result + 18] = I64.from_int(I64.get_max()).to_bytes()[0:8]

        return WasiResult.SUCCESS

    def fd_prestat_dir_name(self, fd: int, name: int, name_len: int) -> tuple[I32]:
        path = self.fs.fds[fd].dirname
        assert path
        self.exec.memory.store(name, f"{path}".encode() + b"\0")
        return WasiResult.SUCCESS

    def path_filestat_get(self, fd: int, flags: int, path: int, path_len: int, buff: int) -> tuple[I32]:
        path_str = self.exec.memory[path : path + path_len].tobytes().decode()
        if path_str not in self.fs.files or not self.fs.files[path_str].exists:
            return WasiResult.BADF

        f = self.fs.files[path_str]
        # if "size" in f:
        #     size = f["size"]
        # elif "file" in f:
        fh = f.buffer
        assert fh
        cur = fh.tell()
        fh.seek(0, 2)
        size = fh.tell()
        fh.seek(cur, 0)

        self.exec.memory[buff : buff + 8] = I64.from_int(1).to_bytes()[0:8]
        self.exec.memory[buff + 8 : buff + 16] = I64.from_int(1).to_bytes()[0:8]
        self.exec.memory[buff + 16 : buff + 17] = I32.from_int(f.type).to_bytes()[0:1]
        self.exec.memory[buff + 17 : buff + 24] = I64.from_int(1).to_bytes()[0:7]
        self.exec.memory[buff + 24 : buff + 32] = I64.from_int(size).to_bytes()[0:8]
        self.exec.memory[buff + 32 : buff + 40] = I64.from_int(0).to_bytes()[0:8]
        self.exec.memory[buff + 40 : buff + 48] = I64.from_int(0).to_bytes()[0:8]
        self.exec.memory[buff + 48 : buff + 56] = I64.from_int(0).to_bytes()[0:8]

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
        path_name = self.exec.memory[path : path + path_len].tobytes().decode()
        if path_name not in self.fs.files.keys():
            return WasiResult.NOENT
        else:
            f = self.fs.files[path_name]
            f.exists = True
            fd_val = f.fd
            self.exec.memory[fd : fd + 4] = I32.from_int(fd_val).to_bytes()[0:4]

            return WasiResult.SUCCESS

    def fd_seek(self, fd: int, offset: int, whence: int, result: int) -> tuple[I32]:
        if fd not in self.fs.fds:
            return WasiResult.BADF

        f = self.fs.fds[fd].buffer
        if not f:
            return WasiResult.INVAL

        f.seek(offset, whence)
        res = f.tell()
        self.exec.memory[result : result + 8] = I64.from_int(res).to_bytes()[0:8]
        return WasiResult.SUCCESS

    def fd_close(self, fd: int):
        if fd not in self.fs.fds:
            return WasiResult.BADF

        f = self.fs.fds[fd].buffer
        if not f:
            return WasiResult.INVAL

        f.seek(0)
        return WasiResult.SUCCESS

    def fd_read(self, fd: int, iovs: int, iovs_len: int, nread: int):
        data_sz = 0
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(self.exec.memory[iov : iov + 4])
            size = I32.from_bits(self.exec.memory[iov + 4 : iov + 8])
            data_sz += int(size)

        data: bytes
        if fd in self.fs.fds:
            b = self.fs.fds[fd]
            if b.buffer:
                data = b.buffer.read(data_sz)

        # if not data:
        #     return WasiResult.BADF

        total_size = 0
        for i in range(iovs_len):
            iov = iovs + 8 * i
            max_space = int(I32.from_bits(self.exec.memory[iov + 4 : iov + 8]))
            space = min(len(data) - total_size, max_space)
            off = I32.from_bits(self.exec.memory[iov : iov + 4])
            size = I32.from_int(space)
            d = data[total_size : total_size + int(size)]
            self.exec.memory.store(int(off), d)
            total_size += len(d)

        self.exec.memory[nread : nread + 4] = I32.from_int(total_size).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def fd_write(self, fd: int, iovs: int, iovs_len: int, nwritten: int) -> tuple[I32]:
        data = b""
        for i in range(iovs_len):
            iov = iovs + 8 * i
            off = I32.from_bits(self.exec.memory[iov : iov + 4])
            size = I32.from_bits(self.exec.memory[iov + 4 : iov + 8])
            data += self.exec.memory[int(off) : int(off) + int(size)].tobytes()

        if fd not in self.fs.fds:
            return WasiResult.BADF

        if self.fs.fds[fd].write:
            self.fs.fds[fd].write(data)  # type: ignore
        elif self.fs.fds[fd].buffer:
            self.fs.fds[fd].buffer.write(data)  # type: ignore

        self.exec.memory[nwritten : nwritten + 4] = I32.from_int(len(data)).to_bytes()[0:4]

        if self.screen:
            self.screen.update_screen()

        return WasiResult.SUCCESS

    def clock_time_get(self, clk_id: int, precision: int, result: int) -> tuple[I32]:
        t = int(time.time_ns())
        self.exec.memory[result : result + 8] = I64.from_int(t).to_bytes()[0:8]
        return WasiResult.SUCCESS

    def proc_exit(self, a: int):
        sys.exit(a)

    def fd_filestat_get(self, a: I32, b: I32):
        return WasiResult.SUCCESS

    # def poll_oneoff(self, in_ptr: int, out_ptr: int, n_subscriptions: int, n_events_ptr: int) -> tuple[I32]:
    #     self.exec.memory[n_events_ptr : n_events_ptr + 4] = I32.from_int(1).to_bytes()[0:4]
    #     self.exec.memory[out_ptr : out_ptr + 8] = I64.from_int(0).to_bytes()[0:8]
    #     self.exec.memory[out_ptr + 8 : out_ptr + 10] = I16.from_int(0).to_bytes()[0:2]
    #     self.exec.memory[out_ptr + 10 : out_ptr + 11] = I8.from_int(0).to_bytes()[0:1]
    #     self.exec.memory[out_ptr + 11 : out_ptr + 19] = I64.from_int(1).to_bytes()[0:8]
    #     self.exec.memory[out_ptr + 19 : out_ptr + 27] = I64.from_int(0).to_bytes()[0:8]

    #     return WasiResult.SUCCESS

    def path_create_directory(self, a: I32, b: I32, c: I32):
        raise Exception("not implemented")

    def fd_fdstat_set_flags(self, a: I32, b: I32):
        return WasiResult.SUCCESS

    def random_get(self, a: I32, b: int):
        rand = random.randint(0, 2**32 - 1)
        self.exec.memory[b : b + 4] = I32.from_int(rand).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def sock_open(self, family: int, sock_type: int, ro_fd_pr: int) -> tuple[I32]:
        socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        fd = self.fs.next_fd()

        self.fs.add(f"<socket:{fd}>", FSModel(fd=fd, type=FileType.REG, sock=socket, exists=True))
        self.exec.memory[ro_fd_pr : ro_fd_pr + 4] = I32.from_int(fd).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def sock_setsockopt(
        self,
        fd: int,
        level: int,
        name: int,
        flag_ptr: int,
        flag_size: int,
    ) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket
        socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, 1)
        return WasiResult.SUCCESS
        flag = I8.from_bits(self.exec.memory[flag_ptr : flag_ptr + flag_size])

        self.socket.setsockopt(level, name, int(flag))

        return WasiResult.SUCCESS

    def sock_bind(self, fd: int, addr: int, port: int) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        off = I32.from_bits(self.exec.memory[addr : addr + 4])
        size = I32.from_bits(self.exec.memory[addr + 4 : addr + 8])

        addr_str = self.exec.memory[int(off) : int(off) + int(size)].tobytes()
        addr_str = ".".join([str(x) for x in addr_str])
        socket.bind((addr_str, port))

        return WasiResult.SUCCESS

    def sock_listen(self, fd: int, backlog: int) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        socket.listen(backlog)
        return WasiResult.SUCCESS

    def sock_shutdown(self, fd: int, how: int) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        socket.close()
        return WasiResult.SUCCESS

    def sock_accept(self, fd: int, ro_fd_ptr: int) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        child_socket, addr = socket.accept()
        child_fd = self.fs.next_fd()
        self.fs.add(f"<socket:{child_fd}>", FSModel(fd=child_fd, type=FileType.REG, sock=child_socket, exists=True))

        self.exec.memory[ro_fd_ptr : ro_fd_ptr + 4] = I32.from_int(child_fd).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def sock_getpeeraddr(self, fd: int, address_ptr: int, address_type_ptr: int, port_ptr: int) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        addr, port = socket.getpeername()
        addr = addr.split(".")
        addr = [int(x) for x in addr]

        self.exec.memory[address_ptr : address_ptr + 4] = I32.from_int(len(addr)).to_bytes()[0:4]
        self.exec.memory[address_type_ptr : address_type_ptr + 4] = I32.from_int(sk.AF_INET).to_bytes()[0:4]
        self.exec.memory[port_ptr : port_ptr + 4] = I32.from_int(port).to_bytes()[0:4]

        return WasiResult.SUCCESS

    def sock_recv(
        self,
        fd: int,
        ri_data: int,
        ri_data_len: int,
        ri_flag: int,
        ro_data_len: int,
        ro_flag: int,
    ) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        data = b""
        for i in range(ri_data_len):
            iov = ri_data + 8 * i
            off = I32.from_bits(self.exec.memory[iov : iov + 4])
            size = I32.from_bits(self.exec.memory[iov + 4 : iov + 8])
            data += socket.recv(int(size))

        total_size = 0
        for i in range(ri_data_len):
            iov = ri_data + 8 * i
            max_space = int(I32.from_bits(self.exec.memory[iov + 4 : iov + 8]))
            space = min(len(data) - total_size, max_space)
            off = I32.from_bits(self.exec.memory[iov : iov + 4])
            size = I32.from_int(space)
            d = data[total_size : total_size + int(size)]
            self.exec.memory.store(int(off), d)
            total_size += len(d)

        self.exec.memory[ro_data_len : ro_data_len + 4] = I32.from_int(total_size).to_bytes()[0:4]
        return WasiResult.SUCCESS

    def sock_send(self, fd: int, si_data_ptr: int, si_data_len: int, si_flags: int, so_data_len_ptr: int) -> tuple[I32]:
        socket = self.fs.fds[fd].sock
        assert socket

        loop = self.exec.memory[si_data_ptr : si_data_ptr + si_data_len]

        data = b""
        for i in range(len(loop)):
            iov = si_data_ptr + 8 * i
            off = I32.from_bits(self.exec.memory[iov : iov + 4])
            size = I32.from_bits(self.exec.memory[iov + 4 : iov + 8])
            data += self.exec.memory[int(off) : int(off) + int(size)].tobytes()

        socket.send(data)
        return WasiResult.SUCCESS


def to_dump(data):
    return "".join([to_decode(x) for x in data])


def to_decode(data: np.uint8):
    try:
        return data.tobytes().decode()
    except Exception:
        return "?"
