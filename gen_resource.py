from io import StringIO


def gen_def_image(script, suffix):
    fg, avatar, bg = set(), set(), set()

    def mysplit(s: str):
        try:
            i = [x.isdigit() for x in s].index(True)
            return s[:i], s[i:]
        except ValueError:
            return s, ''

    for line in script:
        fn = line.rsplit("'")
        # print(fn)
        if "fg_load" in line:
            fg.add(fn[-2])
            continue
        elif "fg_avatar" in line:
            avatar.add(fn[-2])
            continue
        elif "bg_set" in line:
            bg.add(fn[-2])
            continue

    # print(len(fg), len(avatar), len(bg))
    # print(len(fg) + len(avatar) + len(bg))
    '''
    tempcompare = fg.union(avatar).union(bg)
    image = set()
    with open(r'.\def_images.rpy','r') as file:
        for line in file.readlines()[:-1]:
            image.add(''.join(line.split('=')[0].split(' ')[1:]))
    print(len(fg)+len(avatar)+len(bg),len(image))
    print(sorted(image.difference(tempcompare)))
    In Flowers spring:
    > 1759 1767
    > ['bg017b', 'bg017c', 'caution', 'frik0114c', 'srik0717', 'ssuo0901', 'title_base2_t', 'umay0611']
    '''
    define_image = StringIO()
    # characters = set()
    for n, field in zip(('fg', 'bg', 'avatar'), (fg, bg, avatar)):
        define_image.write('# ' + n + '\n')
        for e in list(field):
            if 'fg' == n or 'avatar' == n:
                f = 'fg'
            elif 'bg' == n:
                f = 'bg'
            e1, e2 = mysplit(e)

            if n == 'avatar':
                # characters.add(e1)
                define_image.write('''image %s %s = "images/%simage/%s.%s"''' % (e1, e2, f, e, suffix) + '\n')
                # define_image.write('''image side %s %s = "images/%simage/%s.%s"''' % (e1, e2, f, e, suffix)+ '\r\n')
            else:
                define_image.write('''image %s %s = "images/%simage/%s.%s"''' % (e1, e2, f, e, suffix) + '\n')
    # print(characters)
    return str(define_image.getvalue())


def gen_def_audio(script, suffix):
    voice, se, bgm = set(), set(), set()

    for line in script:
        fn = line.rsplit("'")
        # print(fn)
        if "v_play" in line:
            voice.add(fn[-2])
            continue
        elif "se_play" in line:
            se.add(fn[-2])
            continue
        elif "bgm_play" in line:
            bgm.add(fn[-2])
            continue
        elif "bgm_fadein" in line:
            bgm.add(fn[-2])
            continue

    print(len(voice), len(se), len(bgm))
    print(len(voice) + len(se) + len(bgm))

    define_audio = StringIO()
    for n, field in zip(('voice', 'se', 'bgm'), (voice, se, bgm)):
        define_audio.write('# ' + n + '\n')
        for e in list(field):
            if e[0] in '01234567890':
                define_audio.write(
                    '''define audio.%s = "audio/%s/%s.%s"''' % ('v_' + e.replace('-', '_'), n, e, suffix) + '\n')
            else:
                define_audio.write(
                    '''define audio.%s = "audio/%s/%s.%s"''' % (e.replace('-', '_'), n, e, suffix) + '\n')

    return str(define_audio.getvalue())
