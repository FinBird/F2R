from typing import List

from i2rpy import iga2py
from dumpcode import dump
from gen_resource import gen_def_audio, gen_def_image

def gen_rpy_image_voice(fl: List[str], nl: List[str]):
    l = iga2py(fl)
    for r, n in zip(l, nl):
        print(n)
        with open(n + r'_test.py', 'w+') as f:
            f.write(r)
        with open(n + r'_test.rpy', 'w+') as f2:
            f2.write(dump(r))

        s = r.splitlines()
        with open(n + r'_def_image.rpy', 'w+') as i:
            t = gen_def_image(s, 'avif')
            i.write(t)
        with open(n + r'_def_voice.rpy', 'w+') as v:
            v.write(gen_def_audio(s, 'opus'))

if __name__ == '__main__':
    file_list = [
        r'.\spring\data00.iga',
        r'.\summer\data00.iga',
        r'.\autumn\data00.iga',
        r'.\winter\data00.iga',
    ]
    name_list = ['spring', 'summer', 'autumn', 'winter']
    gen_rpy_image_voice(file_list, name_list)
