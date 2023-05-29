import enum
from io import BytesIO, StringIO
from dataclasses import dataclass
from pprint import pprint
from typing import List, Tuple
from struct import unpack

from md5_table import md5_map

# Modify From https://github.com/shimamura-sakura/FlowerScript
ENCODING = 'cp932'


def le_fr(data, signed=False):
    value = shift = 0
    for b in data:
        value += b << shift
        shift += 8
    if signed and b & 0x80:
        value -= 1 << shift
    return value


def le_to(value, size):
    maxval = 1 << (size * 8)
    if value < 0:
        value += maxval
    if value < 0 or not value < maxval:
        raise ValueError('number out of range')
    return [(value >> (i * 8)) & 0xFF for i in range(size)]


def fmt_number(number, fmt='0x%02x'):
    return fmt % number


def fmt_offset(offset):
    return "'label_0x%x'" % offset

def fmt_offset2(offset):
    return "label_0x%x" % offset

def fmt_list(data):
    return '[%s]' % (', '.join(fmt_number(x) for x in data))


class Type(enum.Enum):
    HEXNUM = 0
    SG_DEC = 1
    UN_DEC = 2
    OFFSET = 3
    STRLEN = 4
    BARRAY = 5
    NULL = 6

class Op:
    def __init__(self, opname):
        self.opname = opname
        self.opsize = 2
        self.fields = []

    def field(self, size, ig_type):
        self.fields.append((size, ig_type))
        self.opsize += size
        return self

    def r(self, fp, encoding, label_set):
        segs = []
        slen = None
        for size, tp in self.fields:
            data = fp.read(size)
            if tp == Type.HEXNUM:
                segs.append(fmt_number(le_fr(data)))
            elif tp == Type.SG_DEC:
                segs.append(fmt_number(le_fr(data, True), '%d'))
            elif tp == Type.UN_DEC:
                segs.append(fmt_number(le_fr(data, False), '%d'))
            elif tp == Type.OFFSET:
                offset = le_fr(data)
                label_set.add(offset)
                segs.append(fmt_offset(offset))
            elif tp == Type.STRLEN:
                slen = le_fr(data)
            elif tp == Type.BARRAY:
                segs.append(fmt_list(data))
            elif tp == Type.NULL:
                continue

        if slen != None:
            data = fp.read(slen)
            if (i := data.find(0)) == -1:
                tail = None
            else:
                data = data[:i]
                # tail = data[i:]
            if encoding == 'gbk':
                data = data.decode(encoding)
                if data.endswith('.s'):data = 's_'+data[:-2]
            segs.append(repr(data))
            #if tail != None:
            #    segs.append(fmt_list(tail))
        if len(segs)!=0:
            return ' op(%s, %s)' % (repr(self.opname), ', '.join(segs))
        else:
            return ' op(%s)' % (repr(self.opname))

OPS = {
    0x00: Op('dlg_str')
    .field(1, Type.NULL)
    .field(1, Type.STRLEN),  # Text
    0x01: Op('exit')
    .field(2, Type.NULL),
    0x02: Op('jmp_script')
    .field(1, Type.NULL)
    .field(1, Type.STRLEN),  # Filename
    0x04: Op('val_set')
    .field(2, Type.UN_DEC)   # Address
    .field(4, Type.SG_DEC),  # Value

    # 0x64 - The 'yuri gauge', which shows a lily flower growing
    # 0x65 - Used during reasoning selections
    # 0x6c - Related to routes and endings

    0x05: Op('val_add')
    .field(2, Type.UN_DEC)   # Address
    .field(4, Type.SG_DEC),  # Value
    0x06: Op('jmp_eq')
    .field(2, Type.NULL)
    .field(2, Type.UN_DEC)   # Address
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC)   # Value
    .field(4, Type.OFFSET),  # Label
    0x08: Op('jmp_be')
    .field(2, Type.NULL)
    .field(2, Type.UN_DEC)   # Address
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC)   # Value
    .field(4, Type.OFFSET),  # Label
    0x09: Op('jmp_le')
    .field(2, Type.NULL)
    .field(2, Type.UN_DEC)   # Address
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC)   # Value
    .field(4, Type.OFFSET),  # Label
    0x0c: Op('dlg_num')
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC),  # ? Sequence Number
    0x0d: Op('jmp')
    .field(2, Type.NULL)
    .field(4, Type.OFFSET),  # Label
    0x0e: Op('wait')
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC),  # Duration (ms)
    0x0f: Op('bg_set') # setBackground
    .field(1, Type.UN_DEC)   # ? Layer always 1,  0 appear in 04a_02500.s eg:cut04x.bmp
    .field(1, Type.STRLEN),  # Filename (w ext)
    0x10: Op('bg_set2')  # setBackgroundAndClearForegroundsAndAvatar
    .field(1, Type.UN_DEC)   # ? Layer
    .field(1, Type.STRLEN),  # Filename (w ext)
    0x11: Op('fg_clear')
    .field(6, Type.NULL),  # clear all fgs and avatar
    0x12: Op('fg_load1')
    .field(1, Type.UN_DEC)   # Layer
    .field(1, Type.STRLEN),  # Filename (w ext)
    0x13: Op('fg_metrics')
    .field(1, Type.UN_DEC)   # Layer
    .field(1, Type.UN_DEC)   # Scale %
    .field(2, Type.SG_DEC)   # X of center
    .field(2, Type.SG_DEC),  # Y of top
    0x14: Op('crossfade')
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC),  # Duration (ms)
    0x16: Op('bg_color')
    .field(2, Type.NULL)
    .field(1, Type.UN_DEC) # R
    .field(1, Type.UN_DEC) # G
    .field(1, Type.UN_DEC) # B
    .field(1, Type.NULL),
    0x1b: Op('sel_end')
    .field(2, Type.NULL),
    0x1c: Op('sel_beg')
    .field(2, Type.NULL),
    0x1d: Op('sel_add')
    .field(2, Type.STRLEN)
    .field(4, Type.OFFSET),
    0x1e: Op('setVisibleEndCompleted')
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC),
    0x21: Op('mark_end')
    .field(2, Type.UN_DEC),  # Ending No. (1-10)
    0x22: Op('bgm_play')
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # Repeat
    .field(3, Type.NULL)
    .field(1, Type.STRLEN),  # Filename (w/o ext; .ogg)
    0x23: Op('bgm_stop')
    .field(2, Type.NULL),
    0x24: Op('bgm_fadeout')
    .field(2, Type.NULL)
    .field(4, Type.SG_DEC),  # Duration (ms)
    0x25: Op('bgm_fadein')
    .field(1, Type.HEXNUM)   # ?: 0, 1 have sound, others no sound
    .field(1, Type.UN_DEC)   # Repeat
    .field(4, Type.SG_DEC)   # Fade in (ms), must be positive
    .field(1, Type.STRLEN)   # Filename (w/o ext; .ogg)
    .field(3, Type.BARRAY),
    0x27: Op('v_play')
    .field(5, Type.NULL)
    .field(1, Type.STRLEN),
    0x28: Op('se_play')
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # Repeat
    .field(3, Type.NULL)
    .field(1, Type.STRLEN),  # Filename (w/o ext; .ogg)
    0x29: Op('se_stop')
    .field(2, Type.NULL),
    0x2a: Op('v_stop')   # ZhangHai - voice stop
    .field(2, Type.NULL),
    0x2c: Op('se_fadeout')   # Fade out SE
    .field(2, Type.NULL)
    .field(4, Type.UN_DEC),  # Duration (ms)
    0x2d: Op('se_fadein')
    .field(1, Type.HEXNUM)   # ?: 0, 1 have sound, others no sound
    .field(1, Type.UN_DEC)   # Repeat
    .field(4, Type.SG_DEC)   # Fade in (ms), must be positive
    .field(1, Type.STRLEN)   # Filename (w/o ext; .ogg)
    .field(3, Type.BARRAY),
    0x35: Op('yuri')
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC),  # 1:Up, 2:Down
    0x36: Op('unknown_0x36')         # Zhanghai - NOP
    .field(1, Type.NULL)
    .field(1, Type.HEXNUM),
    0x3a: Op('setGoodEndCompleted')         # ZhangHai - set good end completed
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC),  # Index
    0x3b: Op('jmp_nishuume')
    .field(2, Type.NULL)
    .field(4, Type.OFFSET),
    0x3f: Op('add_backlog')
    .field(1, Type.NULL)
    .field(1, Type.STRLEN),     # Text
    0x40: Op('dlg_mode')
    .field(2, Type.UN_DEC),       # visible
    0x4c: Op('dlg_clear') # ZhangHai: clear vertical messages
    .field(2, Type.NULL),
    0x4d: Op('dlg_fade')  # ZhangHai: fade window
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # visible
    .field(4, Type.SG_DEC),  # duration ms
    0x50: Op('scr_eff')         # ZhangHai: screen effect (shaking etc.)
    .field(1, Type.HEXNUM)   # ?
    .field(1, Type.HEXNUM)   # additional Count
    .field(4, Type.HEXNUM)   # distance
    .field(4, Type.UN_DEC),  # duration
    0x51: Op('scr_eff_stop')    # ZhangHai
    .field(3, Type.NULL),
    0x54: Op('wait_click')
    .field(2, Type.HEXNUM),  # ZhangHai: 0:Invisible 1:MsgWait 2:MsgWait

    # ZhangHai - https://github.com/zhanghai/igtools/blob/master/igscript/igscript.main.kts#L330
    # TODO: Only used in 04a_02700s.s. Likely related to selection?
    0x57: Op('unknown_0x57')
    .field(2, Type.HEXNUM),
    0x5d: Op('unknown_0x5d')
    .field(2, Type.HEXNUM),
    0x5e: Op('unknown_0x5e')
    .field(2, Type.HEXNUM),
    0x5f: Op('unknown_0x5f')
    .field(2, Type.HEXNUM)
    .field(4, Type.OFFSET),
    0x60: Op('WHAT_THE_FUCK_0x60')
    .field(82, Type.BARRAY),
    0x61: Op('unknown_0x61')
    .field(1, Type.HEXNUM)
    .field(1, Type.HEXNUM),

    0x72: Op('fg_anim_a')
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # Layer
    .field(2, Type.SG_DEC)   # X of center (original size)
    .field(2, Type.SG_DEC)   # Y of top    (original size)
    .field(2, Type.SG_DEC)   # X scale %
    .field(2, Type.SG_DEC)   # Y scale %
    .field(2, Type.SG_DEC)   # Alpha (bigger, positive)
    .field(2, Type.NULL)
    .field(2, Type.SG_DEC)   # do { repeat; n -= 1; } while (n > 0);
    .field(2, Type.NULL),
    0x73: Op('fg_anim_b')
    .field(1, Type.UN_DEC)   # Layer
    .field(1, Type.UN_DEC)   # ? Method (0:?, 1;?, 2:BA, 3:AB, 4:ABA, 5:AB)
    .field(2, Type.SG_DEC)   # X of center (original size)
    .field(2, Type.SG_DEC)   # Y of top    (original size)
    .field(2, Type.SG_DEC)   # X scale %
    .field(2, Type.SG_DEC)   # Y scale %
    .field(2, Type.SG_DEC)   # Alpha (smaller, positive)
    .field(2, Type.NULL)
    .field(2, Type.SG_DEC)   # Duration (ms)
    .field(2, Type.NULL),
    0x74: Op('fg_anim_play')   # anim_run
    .field(2, Type.NULL),
    0x75: Op('fg_anim_stop')    # anim_end
    .field(2, Type.UN_DEC),     # layer
    0x83: Op('unknown_0x83') # Todo: Only appeared in Hiver.
    .field(2, Type.BARRAY)
    .field(4, Type.SG_DEC),
    0x8b: Op('unknown_0x8b')  # TODO: Only appeared in 04a_02700s.s. Likely return to selection?
    .field(2, Type.HEXNUM),
    0x9c: Op('fg_load2')
    .field(1, Type.UN_DEC)   # layer
    .field(1, Type.STRLEN),  # file name
    0xb2: Op('play_video')   # ZhangHai - play video
    .field(2, Type.NULL)
    .field(2, Type.UN_DEC)   # 0: OP, 1: Grand Final ed
    .field(2, Type.NULL),
    0xb3: Op('play_credits')  # ZhangHai - play credits
    .field(1, Type.NULL)
    .field(1, Type.HEXNUM),  # 1: TrueEnd, 3: NormalEnd
    0xb4: Op('fg_avatar')
    .field(1, Type.NULL)
    .field(1, Type.STRLEN),  # FileName
    0xb6: Op('dlg_style')
    .field(2, Type.UN_DEC),  # 0: horizontal bottom, 1: vertical fullscreen
    0xb8: Op('set_chapter')
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC),  # ? Chapter No.
    0xba: Op('unknown_0xba')
    .field(2, Type.HEXNUM),
    0xbb: Op('bgm_vol_bb')   # ZhangHai - fade out music
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # Volume %
    .field(2, Type.UN_DEC)   # Fade out (ms)
    .field(2, Type.NULL),
    0xbc: Op('bgm_vol_bc')   # ZhangHai - fade in music
    .field(1, Type.UN_DEC)   # Volume %
    .field(1, Type.NULL)
    .field(2, Type.UN_DEC)   # Fade in (ms)
    .field(2, Type.NULL),
    0xbd: Op('glb_volume_bd')         # anim global volume
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # Volume %
    .field(2, Type.UN_DEC)   # Fade out (ms)
    .field(2, Type.NULL),
    0xbe: Op('glb_volume_be')         # ZhangHai - fade in all sounds
    .field(1, Type.NULL)
    .field(1, Type.UN_DEC)   # Volume %
    .field(2, Type.UN_DEC)   # Fade in (ms)
    .field(2, Type.NULL),
    0xbf: Op('play_fg_anim')         # ZhangHai - play fg anim
    #.field(1, Type.UN_DEC)   # count
    .field(14, Type.BARRAY), # indices
    0xc0: Op('stop_fg_anim')         # ZhangHai - stop fg anim
    #.field(1, Type.UN_DEC)   # count
    .field(14, Type.BARRAY), # indices
}

OPS_BYNAME = dict(map(lambda kv: (kv[1].opname, (kv[0], kv[1])), OPS.items()))


statistics = {}


def disasm(fp, encoding=ENCODING):
    lines = []
    label_set = set()
    while len(data := fp.read(2)) == 2:
        offset = fp.tell() - 2
        opcode, opsize = data
        if opcode in OPS:
            statistics[opcode] = statistics.get(opcode, 0) + 1
            lines.append((offset, OPS[opcode].r(fp, encoding, label_set)))
        else:
            raise NotImplementedError(
                'unimplemented opcode %02x at offset %x' % (opcode, offset))
        # print(lines[-1])
    i = 0
    while i < len(lines):
        offset, line = lines[i]
        if offset in label_set:
            label_set.remove(offset)
            lines.insert(i, (offset, fmt_offset(offset)))
            i += 1
        i += 1
    if len(label_set) > 0:
        print('- Warning: not all jumps are pointing to an instruction -')
        for offset in label_set:
            text = fmt_offset(offset) + '.define_as(0x%x)' % offset
            print('=>', text)
            continue
            #lines.append((offset, text))
        print('- end of warning -')
    return [x[1] for x in lines]


class Label:
    def __init__(self, asmer, name):
        self.name = name
        self.asmer = asmer

    def add_ref(self, offset, size):
        self.asmer.lbl_refs.append((self.name, offset, size))

    def define(self):
        self.asmer.lbl_offs[self.name] = len(self.asmer.bytes)

    def define_as(self, value):
        self.asmer.lbl_offs[self.name] = value


class Assembler:
    def __init__(self, encoding=ENCODING):
        self.encoding = encoding
        self.bytes = bytearray()
        self.lbl_refs = []
        self.lbl_offs = {}

    def __getattribute__(self, name):
        if name.startswith('label_'):
            return Label(self, name)
        return object.__getattribute__(self, name)

    def finish(self):
        for name, offset, size in self.lbl_refs:
            value = self.lbl_offs[name]
            self.bytes[offset:offset+size] = le_to(value, size)

    def op(self, opname, *args):
        if opname in OPS_BYNAME:
            opcode, op = OPS_BYNAME[opname]
        else:
            raise NotImplementedError('unknown op name %s' % opname)
        self.bytes.append(opcode)
        self.bytes.append(op.opsize)
        slen_off = slen_siz = None
        args = list(args)
        for size, tp in op.fields:
            if tp == Type.HEXNUM or tp == Type.SG_DEC or tp == Type.UN_DEC:
                value = args.pop(0)
                self.bytes.extend(le_to(value, size))
                continue
            if tp == Type.OFFSET:
                label = args.pop(0)
                label.add_ref(len(self.bytes), size)
                self.bytes.extend(le_to(-1, size))
                continue
            if tp == Type.STRLEN:
                slen_off = len(self.bytes)
                slen_siz = size
                self.bytes.extend(le_to(-1, size))
                continue
            if tp == Type.BARRAY:
                array = args.pop(0)
                if len(array) != size:
                    raise ValueError('data length not equal to definition')
                self.bytes.extend(array)
                continue
            raise Exception('should be unreachable !')
        if slen_off != None:
            str_dat = args.pop(0).encode(self.encoding)
            self.bytes.extend(str_dat)
            str_len = len(str_dat)
            if len(args) > 0:
                self.bytes.extend(args[0])
                str_len += len(args[0])
            self.bytes[slen_off:slen_off+slen_siz] = le_to(str_len, slen_siz)



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


# TODO: fix just for igs script archive
# script.iga and data00.iga
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

    # b.read(7)
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

        if not dir[index].is_encrypt:  # Chinese Localize
            dir[index].data = bytes((data[i] ^ (i + 2) ^ xor) & 0xFF for i in range(len(data)))
        else:  # Origin Ver
            dir[index].data = bytes((data[i] ^ (i + 2) ^ xor ^ (0x5C * (i + 1))) & 0xFF for i in range(len(data)))

        continue

    return dir

def symbol_replace(s: str):
    symbol_dict = {'亹': '\\n', '偂': '，',
                   '偅': '。', '偋': '」',
                   '僅': '”', '偉': '、',
                   '僃': '’', '傿': '!',
                   '僁': '？', '偭': '》',
                   '傽': '）', '偐': '』', r'\u3000': '　'}
    for key, value in symbol_dict.items():
        s = s.replace(key, value)
    return s



def iga2s(filepath: str) -> List[Entry]:
    return iga_decode(BytesIO(open(filepath, 'rb').read()))


def s2py(entrys: List[Entry]) -> Tuple[List[Tuple[str, int]], str]:
    txt = StringIO()
    ll = []
    for s in entrys:
        result = disasm(BytesIO(s.data), encoding='gbk')
        txt.write('#BEGIN %s\n' % s.Name)
        txt.write('with Script("s_%s"):' % (s.Name.rsplit('.')[0]))
        indent = 1
        for line in result:
            if 'label_0x' in line and 'op(' not in line:
                if indent == 2:
                    txt.write('\n' + '    with Label("' + line[1:-1] + '"):')
                    continue
                if indent == 1:
                    indent += 1
                    txt.write('\n' + '    with Label("' + line[1:-1] + '"):')
                    continue
            txt.write('\n' + '    ' * indent + line)
        txt.write('\n#END %s\n\n' % (s.Name.rsplit('.')[0]))
        ll.append((s.Name, len(result)))

    return ll, str(txt.getvalue())


def py2rpy(pyf: str) -> str:
    insts = {
        "  op('unknown_0x1e6', ": " unknown_0x1e6(",
        "  op('setVisibleEndCompleted', ": " setVisibleEndCompleted(",
        "  op('unknown_0x36', ": " unknown_0x36(",
        "  op('setGoodEndCompleted', ": " setGoodEndCompleted(",
        "  op('unknown_0x57', ": " unknown_0x57(",
        "  op('unknown_0x5d', ": " unknown_0x5d(",
        "  op('unknown_0x5e', ": " unknown_0x5e(",
        "  op('unknown_0x5f', ": " unknown_0x5f(",
        "  op('unknown_0x61', ": " unknown_0x61(",
        "  op('unknown_0x83', ": " unknown_0x83(",
        "  op('unknown_0x8b', ": " unknown_0x8b(",
        "  op('unknown_0xba', ": " unknown_0xba(",
        "  op('WHAT_THE_FUCK_0x60', ": " WHAT_THE_FUCK_0x60(",
        "  op('add_backlog', ": " add_backlog(",
        "  op('bg_color', ": " bg_color(",
        "  op('bg_set', ": " bg_set(",
        "  op('bg_set2', ": " bg_set2(",
        "  op('bgm_fadein', ": " bgm_fadein(",
        "  op('bgm_fadeout', ": " bgm_fadeout(",
        "  op('bgm_play', ": " bgm_play(",
        "  op('bgm_stop'": " bgm_stop(",
        "  op('bgm_vol_bb', ": " bgm_vol_bb(",
        "  op('bgm_vol_bc', ": " bgm_vol_bc(",
        "  op('crossfade', ": " crossfade(",
        "  op('dlg_clear'": " dlg_clear(",
        "  op('dlg_fade', ": " dlg_fade(",
        "  op('dlg_mode', ": " dlg_mode(",
        "  op('dlg_num', ": " dlg_num(",
        "  op('dlg_str', ": " dlg_str(",
        "  op('dlg_style', ": " dlg_style(",
        "  op('exit'": " exit(",
        "  op('fg_anim_a', ": " fg_anim_a(",
        "  op('fg_anim_b', ": " fg_anim_b(",
        "  op('fg_anim_play'": " fg_anim_play(",
        "  op('fg_anim_stop', ": " fg_anim_stop(",
        "  op('fg_avatar', ": " fg_avatar(",
        "  op('fg_clear'": " fg_clear(",
        "  op('fg_load1', ": " fg_load1(",
        "  op('fg_load2', ": " fg_load2(",
        "  op('fg_metrics', ": " fg_metrics(",
        "  op('glb_volume_bd', ": " glb_volume_bd(",
        "  op('glb_volume_be', ": " glb_volume_be(",
        "  op('jmp_be', ": " jmp_be(",
        "  op('jmp_eq', ": " jmp_eq(",
        "  op('jmp_le', ": " jmp_le(",
        "  op('jmp_nishuume', ": " jmp_nishuume(",
        "  op('jmp_script', ": " jmp_script(",
        "  op('jmp', ": " jmp(",
        "  op('mark_end', ": " mark_end(",
        "  op('play_credits', ": " play_credits(",
        "  op('play_fg_anim', ": " play_fg_anim(",
        "  op('play_video', ": " play_video(",
        "  op('scr_eff_stop', ": " scr_eff_stop(",
        "  op('scr_eff', ": " scr_eff(",
        "  op('se_fadein', ": " se_fadein(",
        "  op('se_fadeout', ": " se_fadeout(",
        "  op('se_play', ": " se_play(",
        "  op('se_stop'": " se_stop(",
        "  op('sel_add', ": " sel_add(",
        "  op('sel_beg'": " sel_beg(",
        "  op('sel_end'": " sel_end(",
        "  op('set_chapter', ": " set_chapter(",
        "  op('stop_fg_anim', ": " stop_fg_anim(",
        "  op('v_play', ": " v_play(",
        "  op('v_stop'": " v_stop(",
        "  op('val_add', ": " val_add(",
        "  op('val_set', ": " val_set(",
        "  op('wait', ": " wait(",
        "  op('wait_click', ": " wait_click(",
        "  op('yuri', ": " yuri(",
        " op('scr_eff_stop')":"scr_eff_stop()",
    }
    for k, v in insts.items():
        pyf = pyf.replace(k, v)
    for suffix in ('.png', '.bmp'):
        pyf = pyf.replace(suffix, '')
    pyf = symbol_replace(pyf)
    return pyf


def iga2py(filepaths: List[str]) -> List[str]:
    rpys = []
    for fp in filepaths:
        entrys = iga2s(fp)
        entrys.sort(key=lambda x: x.Name, reverse=False)
        info, pys = s2py(entrys)
        info.sort(key=lambda x: x[1], reverse=True)
        pprint(info)
        rpy = py2rpy(pys)
        rpys.append(rpy)
    return rpys

if __name__ == '__main__':
    file_list = [
        r'.\spring\data00.iga',
        r'.\summer\data00.iga',
        r'.\autumn\data00.iga',
        r'.\winter\data00.iga',
    ]

    rpys = iga2py(file_list)
    with open(r'.\spring_test.rpy','w+') as f:
        f.write(rpys[0])
    with open(r'.\summer_test.rpy','w+') as f:
        f.write(rpys[1])
    with open(r'.\autumn_test.rpy','w+') as f:
        f.write(rpys[2])
    with open(r'.\winter_test.rpy','w+') as f:
        f.write(rpys[3])
