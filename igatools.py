# py ver: https://github.com/zhanghai/vntools/tree/master/igatool
import os, sys, string
from md5 import md5_map
from typing import List
from dataclasses import dataclass


@dataclass
class Entry:
    name_offset: int = 0
    offset: int = 0
    size: int = 0
    name: str = ""
    encrypted_name: str = ""
    path: str = ""


SEPARATOR: str = '\\' if os.name == 'nt' else '/'  # Separator for paths based on OS.
BUFFER_SIZE: int = 4096  # Read buffer size.
IGA_SIGNATURE: bytes = b'IGA0'  # IGA archive file signature.
IGA_UNKNOWN: bytes = b'\x00\x00\x00\x00'  # Unknown bytes.
IGA_PADDING: bytes = b'\x02\x00\x00\x00\x02\x00\x00\x00'  # Padding bytes.
IGA_ENTRIES_OFFSET: int = len(IGA_SIGNATURE) + len(IGA_UNKNOWN) + len(
    IGA_PADDING)  # The offset where the entries start.
BASE36_CHARACTERS: str = string.digits + string.ascii_lowercase  # Base36 character set.


def usage(program_name: str):
    print(f"Usage: {program_name} -l IGA_FILE", file=sys.stderr)
    print(f"Usage: {program_name} -x IGA_FILE [OUTPUT_DIRECTORY]", file=sys.stderr)
    print(f"Usage: {program_name} -c IGA_FILE INPUT_FILE...", file=sys.stderr)


def get_file_name(path: str) -> str:
    last_separator_index = path.rfind(SEPARATOR)
    if last_separator_index == len(path) - 1:
        raise ValueError(path)
    elif last_separator_index != -1:
        return path[last_separator_index + 1:]
    else:
        return path


# Varint
def read_packed_uint32(stream) -> int:
    value: int = 0
    while True:
        value = (value << 7) | stream.read(1)[0]
        if (value & 1) == 0:
            continue
        else:
            break
    return value >> 1


def write_packed_uint32_byte(stream, byte: int, started: bool, end: bool) -> bool:
    byte &= 0x7f
    started |= byte != 0
    if started or end:
        byte <<= 1
        if end:
            byte |= 0x01
        stream.write(bytes([byte]))
    return started


def write_packed_uint32(stream, value: int):
    started = False
    started |= write_packed_uint32_byte(stream, (value >> 28) & 0x7f, started, False)
    started |= write_packed_uint32_byte(stream, (value >> 21) & 0x7f, started, False)
    started |= write_packed_uint32_byte(stream, (value >> 14) & 0x7f, started, False)
    started |= write_packed_uint32_byte(stream, (value >> 7) & 0x7f, started, False)
    write_packed_uint32_byte(stream, value & 0x7f, started, True)


def read_packed_string(stream, length: int) -> str:
    buffer = []
    for _ in range(length):
        buffer.append(bytes([read_packed_uint32(stream)]))
    return b''.join(buffer).decode('ascii')


def read_last_packed_string(stream, end: int) -> str:
    buffer = []
    while stream.tell() < end:
        buffer.append(bytes([read_packed_uint32(stream)]))
    return b''.join(buffer).decode('ascii')


def write_packed_string(stream, value: str):
    buffer = value.encode('ascii')
    for byte in buffer:
        write_packed_uint32(stream, byte)


def extract(iga_path: str, is_list: bool, output_directory: str):
    """
    Extracts files from an IGA archive.

    Args:
        iga_path (str): The path to the IGA archive file.
        is_list (bool): If True, lists the files in the archive, otherwise extracts them.
        output_directory (str): The output directory for extracted files.
    """
    if not is_list and not os.path.exists(output_directory):  # 创建文件夹
        os.makedirs(output_directory)

    with open(iga_path, 'rb') as iga_file:
        signature = iga_file.read(len(IGA_SIGNATURE))
        if signature != IGA_SIGNATURE:
            print(f"Unexpected signature: {signature.hex()}", file=sys.stderr)
            sys.exit(1)

        iga_file.seek(0, os.SEEK_END)
        file_size: int = iga_file.tell()

        iga_file.seek(IGA_ENTRIES_OFFSET)
        entries_length: int = read_packed_uint32(iga_file)
        entries_end: int = iga_file.tell() + entries_length

        entries: List[Entry] = []
        while iga_file.tell() < entries_end:
            entry = Entry()
            entry.name_offset = read_packed_uint32(iga_file)
            entry.offset = read_packed_uint32(iga_file)
            entry.size = read_packed_uint32(iga_file)
            entries.append(entry)

        names_length: int = read_packed_uint32(iga_file)
        names_end: int = iga_file.tell() + names_length

        for i, entry in enumerate(entries):
            if i < len(entries) - 1:
                name_length = entries[i + 1].name_offset - entry.name_offset
                name = read_packed_string(iga_file, name_length)
            else:
                name = read_last_packed_string(iga_file, names_end)

            if len(name) == 12 and set(name).issubset(BASE36_CHARACTERS):
                entry.encrypted_name = name
                if name in md5_map.keys():
                    entry.name = md5_map[name]
                else:
                    print(f"Warning: Unknown encrypted name: {name}", file=sys.stderr)
                    entry.name = name
            else:
                entry.name = name
            entry.offset += names_end

            if not is_list:
                entry.path = output_directory + SEPARATOR + entry.name

            if entry.offset + entry.size > file_size:
                raise ValueError(f"Entry offset: {entry.offset}, size: {entry.size}, file size: {file_size}")

        if is_list:
            for entry in entries:
                print(entry.name)
            return

        for entry in entries:
            # print(entry.name)
            with open(entry.path, 'wb') as output_file:
                iga_file.seek(entry.offset)
                is_script = entry.name.endswith(".s")
                size = 0
                while size < entry.size:
                    transfer_size = min(BUFFER_SIZE, entry.size - size)
                    buffer = bytearray(iga_file.read(transfer_size))
                    for i in range(transfer_size):
                        key = (i + 2)
                        if is_script:
                            key ^= 0xFF
                            if entry.encrypted_name:
                                key ^= 0x5C * (i + 1)
                        buffer[i] ^= key & 0xFF
                    output_file.write(bytes(buffer))
                    size += transfer_size


def compress(iga_path: str, input_paths: List[str]):
    """
    Compresses a list of files into an IGA archive.

    Args:
        iga_path (str): The output path for the IGA archive file.
        input_paths (List[str]): A list of paths to the input files.
    """
    with open(iga_path, 'wb') as iga_file:
        iga_file.write(IGA_SIGNATURE)
        iga_file.write(IGA_UNKNOWN)
        iga_file.write(IGA_PADDING)

        entries: List[Entry] = []
        for input_path in input_paths:
            entry = Entry()
            entry.path = input_path
            entries.append(entry)

        names_stream = b""
        name_offset = 0
        for entry in entries:
            entry.name_offset = name_offset
            entry.name = get_file_name(entry.path)
            buffer = bytearray()
            write_packed_string(buffer, entry.name)
            names_stream += buffer
            name_offset += len(entry.name)

        offset = 0
        for entry in entries:
            entry.offset = offset
            with open(entry.path, 'rb') as input_file:
                input_file.seek(0, os.SEEK_END)
                entry.size = input_file.tell()
                offset += entry.size

        entries_stream = b""
        for entry in entries:
            buffer = bytearray()
            write_packed_uint32(buffer, entry.name_offset)
            write_packed_uint32(buffer, entry.offset)
            write_packed_uint32(buffer, entry.size)
            entries_stream += buffer

        entries_length = len(entries_stream)
        buffer = bytearray()
        write_packed_uint32(buffer, entries_length)
        iga_file.write(buffer)
        iga_file.write(entries_stream)

        names_length = len(names_stream)
        buffer = bytearray()
        write_packed_uint32(buffer, names_length)
        iga_file.write(buffer)
        iga_file.write(names_stream)

        for entry in entries:
            with open(entry.path, 'rb') as input_file:
                is_script = entry.name.endswith(".s")
                size = 0
                while size < entry.size:
                    transfer_size = min(BUFFER_SIZE, entry.size - size)
                    buffer = bytearray(input_file.read(transfer_size))
                    for i in range(transfer_size):
                        key = (i + 2) ^ 0xFF if is_script else i + 2
                        buffer[i] ^= key
                    iga_file.write(bytes(buffer))
                    size += transfer_size


def main():
    if len(sys.argv) < 2:
        usage(sys.argv[0])
        sys.exit(1)

    if sys.argv[1] == "-l":
        if len(sys.argv) != 3:
            usage(sys.argv[0])
            sys.exit(1)
        extract(sys.argv[2], True, ".")
    elif sys.argv[1] == "-x":
        if not (len(sys.argv) == 3 or len(sys.argv) == 4):
            usage(sys.argv[0])
            sys.exit(1)
        output_directory = sys.argv[3] if len(sys.argv) == 4 else "."
        extract(sys.argv[2], False, output_directory)
    elif sys.argv[1] == "-c":
        if len(sys.argv) < 3:
            usage(sys.argv[0])
            sys.exit(1)
        input_files = sys.argv[3:]
        compress(sys.argv[2], input_files)
    else:
        usage(sys.argv[0])
        sys.exit(1)


if __name__ == "__main__":
    main()
    # extract(r'.\iga\winter\script.iga', False, r'.\iga\winter\script')
    # python igatools.py -x .\iga\winter\script.iga .\iga\winter\script