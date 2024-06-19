from typing import Union


class ByteReader:
    """バイト列を読み取るためのクラス"""

    def __init__(self, data: bytes):
        self.data = data
        self.pointer = 0

    def read_byte(self, read_only=False) -> int:
        """ポインタが指す位置のバイトを読み取り、ポインタを進める"""
        byte = self.data[self.pointer]
        if not read_only:
            self.pointer += 1
        return byte

    def read_bytes(self, n: int, read_only=False) -> "ByteReader":
        """ポインタが指す位置からnバイトを読み取り、ポインタを進める"""
        bytes = self.data[self.pointer : self.pointer + n]
        if not read_only:
            self.pointer += n
        return ByteReader(bytes)

    def read_leb128(self) -> int:
        """ポインタが指す位置からLEB128形式の数値を読み取り、ポインタを進める"""
        result = 0
        shift = 0
        while True:
            byte = self.read_byte()
            result |= (byte & 0x7F) << shift
            shift += 7
            if byte & 0x80 == 0:
                break
        return result

    def read_sleb128(self) -> int:
        """ポインタが指す位置からSLEB128形式の数値を読み取り、ポインタを進める"""
        result = 0
        shift = 0
        while True:
            byte = self.read_byte()
            result |= (byte & 0x7F) << shift
            shift += 7
            if byte & 0x80 == 0:
                break
        if byte & 0x40:
            result |= -(1 << shift)
        return result

    def has_next(self) -> bool:
        """ポインタが指す位置がバイト列の最後かどうかを返す"""
        return self.pointer < len(self.data)

    def copy(self):
        """現在の状態をコピーして新しいByteReaderを返す"""
        return ByteReader(self.data[self.pointer :])

    def __eq__(self, other: Union["ByteReader", bytes]):
        """他のByteReaderと等しいかどうかを返す"""
        if isinstance(other, ByteReader):
            return self.data == other.data
        elif isinstance(other, bytes):
            return self.data == other
        else:
            return False

    def __ne__(self, other: Union["ByteReader", bytes]):
        """他のByteReaderと異なるかどうかを返す"""
        return not self.__eq__(other)

    def __repr__(self):
        """デバッグ用の文字列表現を返す"""
        return f"ByteReader({self.data})"
