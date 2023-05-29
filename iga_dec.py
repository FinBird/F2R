from struct import unpack
from io import BytesIO
from md5_table import md5_map
from dataclasses import dataclass


def ReadPackedUInt(b: BytesIO) -> int:
    val = 0
    while (val & 1) == 0:
        val = val << 7 | unpack('<B', b.read(1))[0]
    return val >> 1


def ReadPackedString(b: BytesIO, length: int) -> str:
    out = bytearray(length)
    for i in range(length):
        out[i] = ReadPackedUInt(b) & 0xFF
    return out.decode('cp932')


def ReadPackedString1(b: BytesIO, end: int):
    out = bytearray()
    while b.tell() < end:
        out.append(ReadPackedUInt(b))
    return out.decode('ascii')


@dataclass
class Entry:
    NameOffset: int = 0
    Offset: int = 0
    Size: int = 0
    Name: str = ''
    data: bytes = b''
    is_encrypt: bool = False


# Warning: Just for decompress script.iga and data00.iga archive
def iga_decode(b: BytesIO):
    assert b.read(4) == b'IGA0'
    b.read(12)
    # b.seek(0x10)
    index_length = ReadPackedUInt(b)
    end_pos = 10 + index_length
    print(index_length, end_pos)

    dir = []
    while b.tell() < end_pos:
        e = Entry(NameOffset=ReadPackedUInt(b), Offset=ReadPackedUInt(b), Size=ReadPackedUInt(b))
        dir.append(e)

    dir.append(Entry(NameOffset=ReadPackedUInt(b), Offset=ReadPackedUInt(b), Size=ReadPackedUInt(b)))
    names_length = ReadPackedUInt(b)
    data_offset = b.tell() + names_length

    for i in range(len(dir)):
        entry = dir[i]
        if i + 1 < len(dir):
            name_length = dir[i + 1].NameOffset - entry.NameOffset
            Name = ReadPackedString(b, name_length)
        else:
            # name_length = names_length - entry.NameOffset
            Name = ReadPackedString1(b, data_offset)

        if len(Name) == 12 and set(Name).issubset(set('0123456789abcdefghijklmnopqrstuvwxyz')):
            try:
                dir[i].Name = md5_map[Name]
                dir[i].is_encrypt = True
                # print(i, dir[i].Name, dir[i].Size)
            except:
                raise
        else:
            dir[i].Name = Name
            print(i, dir[i].Name, dir[i].Size)

        dir[i].Offset += data_offset

    file = b.getvalue()
    for index in range(len(dir)):
        data = bytes(file[dir[index].Offset:dir[index].Offset + dir[index].Size])

        if dir[index].Name.endswith('.s'):  # .igs
            xor = 0xFF
        else:  # others
            dir[index].is_encrypt = False

        if not dir[index].is_encrypt:  # Origin Ver
            dir[index].data = bytes((data[i] ^ (i + 2) ^ xor) & 0xFF for i in range(len(data)))
        else:  # ZH Ver
            # See https://www.bilibili.com/video/av728784563 
            # data[i] = data[i] ^ ((0x5c * (i+1)) & 0xFF) ^ 0xFF
            dir[index].data = bytes((data[i] ^ (i + 2) ^ xor ^ (0x5C * (i + 1))) & 0xFF for i in range(len(data)))

        continue

    return dir

if __name__ == '__main__':
    # winter
    iga_decode(BytesIO(open(r'.\iga\winter\script.iga', 'rb').read()))
    iga_decode(BytesIO(open(r'.\iga\winter\data00.iga', 'rb').read()))
    # spring
    iga_decode(BytesIO(open(r'.\iga\spring\script.iga', 'rb').read()))
    iga_decode(BytesIO(open(r'.\iga\spring\data00.iga', 'rb').read()))
    # autumn
    iga_decode(BytesIO(open(r'.\iga\autumn\script.iga', 'rb').read()))
    iga_decode(BytesIO(open(r'.\iga\autumn\data00.iga', 'rb').read()))
    # summer
    iga_decode(BytesIO(open(r'.\iga\summer\script.iga', 'rb').read()))
    iga_decode(BytesIO(open(r'.\iga\summer\data00.iga', 'rb').read()))
