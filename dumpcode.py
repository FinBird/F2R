import re
from io import StringIO
from functools import cache
from typing import Dict, List

S = ''
s = StringIO()
Indent = 0
behind = ''
who = ''
avatar = ''

layer0 = dict(a=dict(), b=dict(), name='', is_show=False)
layer1 = dict(a=dict(), b=dict(), name='', is_show=False)
layer2 = dict(a=dict(), b=dict(), name='', is_show=False)
layer3 = dict(a=dict(), b=dict(), name='', is_show=False)
layer4 = dict(a=dict(), b=dict(), name='', is_show=False)
layer5 = dict(a=dict(), b=dict(), name='', is_show=False)
layer6 = dict(a=dict(), b=dict(), name='', is_show=False)
layer = [layer0, layer1, layer2, layer3, layer4, layer5, layer6]

fg_load1_layer = dict()  # type: Dict[int,str]
fg_load1_layer_b = dict()
fg_m_list = []
fg_hide_list = ['', '', '', '', '']

first = True
choice = []


def dump(code: str) -> str:
    global S, s, Indent, behind, who, avatar, first

    S = ''
    s = StringIO()
    Indent = 0
    behind = ''
    who = ''
    avatar = ''
    first = True
    choice = []

    global layer, layer0, layer1, layer2, layer3, layer4, layer5, layer6

    layer0 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer1 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer2 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer3 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer4 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer5 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer6 = dict(a=dict(), b=dict(), name='', is_show=False)
    layer = [layer0, layer1, layer2, layer3, layer4, layer5, layer6]

    global fg_load1_layer, fg_load1_layer_b, fg_m_list, fg_hide_list

    fg_load1_layer = dict()  # type: Dict[int,str]
    fg_load1_layer_b = dict()
    fg_m_list = []
    fg_hide_list = ['', '', '', '', '']

    def log(func):
        def wrapper(*args, **kwargs):
            global s
            if kwargs == {} and args == ():
                s.write(gen_I() + '# ' + func.__name__ + '()\n')
                result = func(*args, **kwargs)
                # do something after `sum`
                return result
            if kwargs != {}:
                s.write(gen_I() + '# ' + func.__name__ + '(')
                l = []
                for k, v in kwargs.items():
                    l.append(k + '=' + str(v))
                s.write(', '.join(l) + ')' + '\n')
            if args != ():
                s.write(gen_I() + '# ' + func.__name__ + '(')
                l = []
                for v in args:
                    l.append(str(v).replace('\n', r'\n'))
                s.write(', '.join(l) + ')' + '\n')
            result = func(*args, **kwargs)
            # do something after `sum`
            return result

        return wrapper

    class Script:
        def __init__(self, fileName):
            self.fn = fileName

        def __enter__(self):
            global Indent, s
            Indent += 1
            s = StringIO()
            s.write('label ' + self.fn + ':\n')

        def __exit__(self, exc_type, exc_val, exc_tb):
            global S, s, Indent
            Indent -= 1
            S = S + s.getvalue()
            s = StringIO()

    class Label:
        def __init__(self, LName):
            self.ln = LName

        def __enter__(self):
            global Indent, s
            Indent += 1
            s.write('label ' + self.ln + ':\n')

        def __exit__(self, exc_type, exc_val, exc_tb):
            global S, s, Indent
            Indent -= 1
            S = S + s.getvalue()
            s = StringIO()

    @cache
    def gen_I():
        global Indent
        return '    ' * Indent

    @cache
    def gen_I2(i):
        global Indent
        return '    ' * (Indent + i)

    # 0x04
    @log
    def val_set(index, value):  # type: (int,int) -> None
        s.write('%s$var[%s] = %s\n' % (gen_I(), index, value))

    # 0xb8
    @log
    def set_chapter(index):  # type: (int) -> None
        s.write('%s$chapter = %s\n' % (gen_I(), index))

    # 0x02
    @log
    def jmp_script(Label):  # type: (str) -> None
        s.write('%sjump %s\n' % (gen_I(), Label))

    # 0x01
    @log
    def exit():  # type: () -> None
        s.write('%sreturn\n' % gen_I())

    # 0x16
    @log
    def bg_color(R, G, B):  # type: (int,int,int) -> None
        # for l in ('l0','l1','l2','l3','l4'):
        #    s.write(gen_I()+'scene onlayer '+l+'\n')
        s.write(gen_I() + 'scene onlayer l0\n')
        s.write(gen_I() + 'scene onlayer l1\n')
        s.write(gen_I() + 'scene onlayer l2\n')
        s.write(gen_I() + 'scene onlayer l3\n')
        s.write(gen_I() + 'scene onlayer l4\n')
        s.write(gen_I() + 'scene onlayer l5\n')
        s.write(gen_I() + 'scene onlayer l6\n')
        s.write(gen_I() + 'show expression Solid((%s, %s, %s, 255))\n' % (R, G, B))

    # 0x14
    def crossfade(Duration):  # type: (int) -> None
        # renpy.with_statement(Fade(out_time=float(Duration) / 1000, hold_time=0.0, in_time=0.0))  # type: ignore
        global behind, fg_m_list
        if behind == 'bg_set2' or behind == 'bg_set':
            s.write(' with fade\n')
            behind = ''
            return
        if behind == 'fg_metrics':
            for f in fg_m_list:
                s.write(f.format('with Dissolve(%s)' % (Duration / 1000.0)))
            fg_m_list = []
            behind = ''
            return
        s.write(gen_I() + 'with Dissolve(%s)\n' % (Duration / 1000.0))
        s.write(gen_I() + f'# crossfade({Duration})\n')

    # 0x0e
    @log
    def wait(Duration):  # type: (int) -> None
        s.write(gen_I() + 'pause %s\n' % (Duration / 1000.0))

    def mysplit(s: str):
        try:
            i = [x.isdigit() for x in s].index(True)
            return ' '.join([s[:i], s[i:]])
        except ValueError:
            return s

    # 0x9c
    @log
    def fg_load2(Layer, FileName):  # type: (int,str) -> None
        global layer
        # print(Layer,FileName)
        layer[Layer]['name'] = mysplit(FileName)

    # 0x72
    @log
    def fg_anim_a(Layer, centerX, topY, scaleX, scaleY, alpha, loop):  # type: (int,int,int,int,int,int,int) -> None
        global layer
        layer[Layer]['a'].update(Layer=Layer, centerX=int(centerX), topY=int(topY),
                                 scaleX=int(scaleX), scaleY=int(scaleY), alpha=int(alpha), loop=bool(int(loop)))

    # 0x73
    @log
    def fg_anim_b(Layer, Method, centerX, topY, scaleX, scaleY, alpha,
                  duration):  # type: (int,int,int,int,int,int,int,int) -> None
        global layer
        layer[Layer]['is_show'] = False
        layer[Layer]['b'].update(Layer=Layer, Method=int(Method), centerX=int(centerX), topY=int(topY),
                                 scaleX=int(scaleX), scaleY=int(scaleY), alpha=int(alpha),
                                 duration=int(duration))

    # 0x74
    @log
    def fg_anim_play():
        ''' show t_suo 0001 onlayer l1:
                parallel:
                    alpha 0.00
                    linear 1.0 alpha 1.00
                on hide:
                    xpos 640
                    ypos 0
                    alpha 1.00
        '''
        global layer, layer0, layer1, layer2, layer3, layer4, layer5, layer6
        for ln, l in zip(('l0', 'l1', 'l2', 'l3', 'l4', 'l5', 'l6'),
                         (layer0, layer1, layer2, layer3, layer4, layer5, layer6)):

            if l['a'] and l['b']:
                if l['is_show']:
                    continue
                else:
                    l['is_show'] = True
                s.write(gen_I() + 'show %s onlayer %s' % (l['name'], ln))
                if l['a']['centerX'] != l['b']['centerX']:
                    s.write(':\n')
                    s.write(gen_I2(1) + 'parallel:\n')
                    s.write(gen_I2(2) + 'xpos %s\n' % l['a']['centerX'])
                    s.write(gen_I2(2) + 'linear %s xpos %s\n' % (l['b']['duration'] / 1000.0, l['b']['centerX']))
                    s.write(gen_I2(1) + 'on hide:\n')
                    s.write(gen_I2(2) + 'xpos %s\n' % l['b']['centerX'])
                    s.write(gen_I2(2) + 'ypos %s\n' % l['b']['topY'])
                    s.write(gen_I2(2) + 'alpha %.2f\n' % (l['b']['alpha'] / 255.0))
                    continue
                if l['a']['topY'] != l['b']['topY']:
                    s.write(':\n')
                    s.write(gen_I2(1) + 'parallel:\n')
                    s.write(gen_I2(2) + 'ypos %s\n' % l['a']['topY'])
                    s.write(gen_I2(2) + 'linear %s ypos %s\n' % (l['b']['duration'] / 1000.0, l['b']['topY']))
                    s.write(gen_I2(1) + 'on hide:\n')
                    s.write(gen_I2(2) + 'xpos %s\n' % l['b']['centerX'])
                    s.write(gen_I2(2) + 'ypos %s\n' % l['b']['topY'])
                    s.write(gen_I2(2) + 'alpha %.2f\n' % (l['b']['alpha'] / 255.0))
                    continue
                if l['a']['alpha'] != l['b']['alpha']:
                    s.write(':\n')
                    s.write(gen_I2(1) + 'parallel:\n')
                    s.write(gen_I2(2) + 'alpha %.2f\n' % (l['a']['alpha'] / 255.0))
                    s.write(
                        gen_I2(2) + 'linear %s alpha %.2f\n' % (l['b']['duration'] / 1000.0, l['b']['alpha'] / 255.0))
                    s.write(gen_I2(1) + 'on hide:\n')
                    s.write(gen_I2(2) + 'xpos %s\n' % l['b']['centerX'])
                    s.write(gen_I2(2) + 'ypos %s\n' % l['b']['topY'])
                    s.write(gen_I2(2) + 'alpha %.2f\n' % (l['b']['alpha'] / 255.0))
                    continue
                s.write(':\n')
                s.write(gen_I2(1) + 'on hide:\n')
                s.write(gen_I2(2) + 'xpos %s\n' % l['b']['centerX'])
                s.write(gen_I2(2) + 'ypos %s\n' % l['b']['topY'])
                s.write(gen_I2(2) + 'alpha %.2f\n' % (l['b']['alpha'] / 255.0))
                s.write('\n')

        s.write(gen_I() + 'pause\n')

    # 0x27
    @log
    def v_play(fileName):  # type: (str) -> None
        if fileName[0].isdigit(): fileName = 'v_' + fileName
        fileName = fileName.replace('-', '_')
        s.write(gen_I() + 'play sound audio.%s\n' % fileName)

    # 0x3f
    @log
    def add_backlog(Text):  # type: (str) -> None
        Text = Text.replace('\n', r'\n')
        s.write(gen_I() + "$ narrator.add_history(kind='adv', who='', what='%s')\n" % Text)

    # 0x75
    @log
    def fg_anim_stop(index):  # type: (int) -> None
        global layer0, layer1, layer2, layer3, layer4, layer5, layer6
        # s.write(gen_I() + 'hide %s onlayer l%s\n' % (eval("layer%s['name']" % index), index))

    # 0x2a
    @log
    def v_stop():  # type: () -> None
        s.write(gen_I() + 'stop sound\n')

    # 0x40
    @log
    def dlg_mode(visible):  # type: (int) -> None
        if visible == 1:
            s.write(gen_I() + 'window show\n')
        elif visible == 0:
            s.write(gen_I() + 'window hide\n')

    # 0x00
    @log
    def dlg_str(Text):  # type: (str) -> None
        global who
        if Text.startswith('仈') and who == '':  # type: ignore
            who = Text[1:]
        else:
            # Replace '\n' with r'\n'
            Text = Text.replace('\n', r'\n')

            # Ruby Text
            # Example:
            # dlg_str(「花菱同学的姓氏里含有“<花菱草<加州罂粟>”，它和常用作家纹的花菱纹很像，因而得名。」)
            # "「花菱同学的姓氏里含有“{rb}花菱草{/rb}{rt}加州罂粟{/rt}”，它和常用作家纹的花菱纹很像，因而得名。」"
            ''' Add `ruby_style style.ruby_style` In `style say_dialogue`
                Then:
                   style ruby_style:
                       size 13
                       yoffset -20     
            '''
            for _ in range(Text.count('>')):
                Text = Text.replace('<', '{rb}', 1)
                Text = Text.replace('<', '{/rb}{rt}', 1)
                Text = Text.replace('>', '{/rt}', 1)

            # Todo:Too complex, give up...
            # English Words with '_' suffix should be 'bigger'
            # Example:
            # '「……大家好，我是沙沙2_号！」' -> '「……大家好，我是沙沙{b}2{/b}号！」'
            # "石楠科植物的英文被叫做Heath_" -> 石楠科植物的英文被叫做{b}Heath{/b}
            # '「校园种姓啦。你大概是<学霸< _Brain_>级别的吧。虽然真正用头脑的是白羽。」' -> ?
            # '「Alpen _Hazel，Barbarossa……这些还算是普通的品种名。」' -> ?
            # "「来来来，谁都可以，Let's _try！」" -> ?
            # 「……这样啊。原来是在苏芳君用了<可伦坡技巧<Columbo technique_>的时候啊——」 -> ?
            # 「Xi Yan Mo_是什么呀？」 -> ?
            # 「是La Mesa_吧？」
            '''
            big_words = []
            for word in re.finditer('[_]*[0-9.|a-zA-Z]+_',Text):
                big_words.append((word.group(0), word.group(0)[:-1]))

            for rep in big_words:
                Text = Text.replace(rep[0], '{b}' + rep[1] + '{/b}')
            '''
            if who != '':
                s.write(gen_I() + '"%s"  "%s"\n' % (who, Text))
                who = ''
            else:
                s.write(gen_I() + '"%s"\n' % Text)

    # 0x0c
    @log
    def dlg_num(index):  # type: (int) -> None
        """Todo"""

    # 0x10
    @log
    def bg_set2(Layer, FileName):  # type: (int,str) -> None
        global behind
        behind = 'bg_set2'
        s.write(gen_I() + 'scene %s' % mysplit(FileName))

    # 0x22
    @log
    def bgm_play(Repeat, fileName):  # type: (int,str) -> None
        fileName = fileName.replace('-', '_')
        if Repeat == 1:
            s.write(gen_I() + 'play music audio.%s\n' % fileName)
        elif Repeat == 0:
            s.write(gen_I() + 'play music audio.%s noloop\n' % fileName)

    # 0x0f
    @log
    def bg_set(Layer, FileName):  # type: (int,str) -> None
        global behind
        behind = 'bg_set'
        s.write(gen_I() + 'scene %s' % mysplit(FileName))

    # 0x23
    @log
    def bgm_stop():  # None -> None
        s.write(gen_I() + 'stop music\n')

    # 0x24
    @log
    def bgm_fadeout(Duration):  # type: (int) -> None
        s.write(gen_I() + 'stop music fadeout %.1f\n' % (Duration / 1000.0))

    # 0x25
    @log
    def bgm_fadein(have_sound, Repeat, Duration, _, fileName):  # type: (int,int,int,List[int],str) -> None
        fileName = fileName.replace('-', '_')
        # From 島村桜:
        # ?: 0, 1 have sound, others no sound
        if have_sound not in (0, 1):
            return
        if Repeat == 1:
            s.write(gen_I() + 'play music audio.%s fadein %.1f\n' % (fileName, Duration / 1000.0))
        elif Repeat == 0:
            s.write(gen_I() + 'play music audio.%s noloop fadein %.1f\n' % (fileName, Duration / 1000.0))

    # 0xbb
    @log
    def bgm_vol_bb(volume, duration):  # type:(int,int) -> None
        s.write(gen_I() + "$ renpy.music.set_volume(volume=%.2f, delay=%.1f, channel='music')\n" % (
        volume / 100.0, duration / 1000.0))

    # 0xbc
    @log
    def bgm_vol_bc(volume, duration):  # type:(int,int) -> None
        s.write(gen_I() + "$ renpy.music.set_volume(volume=%.2f, delay=%.1f, channel='music')\n" % (
        volume / 100.0, duration / 1000.0))

    # 0xbd
    @log
    def glb_volume_bd(volume, duration):  # type:(int,int) -> None
        s.write(gen_I() + "$ renpy.music.set_volume(volume=%.2f, delay=%.1f, channel='sound')\n" % (
        volume / 100.0, duration / 1000.0))

    # 0xbe
    @log
    def glb_volume_be(volume, duration):  # type:(int,int) -> None
        s.write(gen_I() + "$ renpy.music.set_volume(volume=%.2f, delay=%.1f, channel='sound')\n" % (
        volume / 100.0, duration / 1000.0))

    # 0x1e
    @log
    def setVisibleEndCompleted(index):  # type:(int) -> None
        # TODO:Mark it in persistent?
        # Only appeared in summer and autumn and only called for non-virtual ends.
        pass

    # 0x57
    @log
    def unknown_0x57(index):  # type:(int) -> None
        # Only appeared in Ete - Hiver and called for non-bad ends.
        # 0 for Ete and Automne called
        # 1 for Good End and 2 for Grand Finale in Hiver (otherwise not called).
        # TODO: Related to game start animation? In Hiver, Neri and Yuzuyuzu are not in Open Video at first round.
        pass

    # 0x12
    @log
    def fg_load1(Layer, FileName):  # type: (int,str) -> None
        global fg_load1_layer
        fg_load1_layer[Layer] = mysplit(FileName)

    # 0xbf
    @log
    def play_fg_anim(indices):  # type:(List[int]) -> None
        """TODO"""

    # 0xc0
    @log
    def stop_fg_anim(indices):  # type:(List[int]) -> None
        """TODO"""

    # 0x13
    @log
    def fg_metrics(Layer, scale, centerX, topY):  # type: (int,int,int,int) -> None
        global fg_load1_layer, fg_load1_layer_b, behind, fg_hide_list
        behind = 'fg_metrics'
        _s = StringIO()
        try:
            _s.write(gen_I() + 'show %s {0}:\n' % fg_load1_layer[Layer])
            # _s.write(gen_I() + 'show %s onlayer l%s:\n'%(fg_load1_layer[Layer],Layer))
            fg_hide_list[Layer] = fg_load1_layer[Layer]
        except KeyError:
            return
            # _s.write(gen_I() + 'show %s onlayer l%s:\n' % (fg_load1_layer_b[Layer], Layer))
        _s.write(gen_I2(1) + 'xcenter %.2f\n' % (centerX / 1280.0))
        _s.write(gen_I2(1) + 'yalign %.2f\n' % (topY / 720.0))
        _s.write(gen_I2(1) + 'zoom %.2f\n' % (scale / 100.0))
        global fg_m_list
        fg_m_list.append(_s.getvalue())

    # 0x54
    @log
    def wait_click(type_):  # type: (int) -> None
        # TODO
        # 0: Invisible click wait
        # 1: Message click wait, seems identical to 2 and only appeared once in 04a_06400.s,
        #    though the window is invisible at that time
        # 2: Message click wait
        s.write(gen_I() + 'pause\n')

    # 0x11
    @log
    def fg_clear():  # type: () -> None
        global fg_load1_layer, fg_load1_layer_b, avatar
        for fn in fg_load1_layer.values():
            s.write(gen_I() + 'hide %s\n' % fn)
        if avatar != '':
            s.write(gen_I() + 'hide %s onlayer face at left\n' % avatar)
        avatar = ''
        fg_load1_layer_b = fg_load1_layer.copy()
        fg_load1_layer.clear()

    # 0xb4
    @log
    def fg_avatar(fileName):  # type: (str) -> None
        global avatar
        avatar = mysplit(fileName)
        s.write(gen_I() + 'scene onlayer face\n')
        s.write(gen_I() + 'show %s onlayer face at Transform(pos=(0.04,0.75))\n' % (mysplit(fileName)))

    # 0x28
    @log
    def se_play(loop, FileName):  # type: (int,str) -> None
        if FileName[0].isdigit(): FileName = 'v_' + FileName
        FileName = FileName.replace('-', '_')
        if loop == 0:
            s.write(gen_I() + 'play sound audio.%s noloop\n' % FileName)
        elif loop == 1:
            s.write(gen_I() + 'play sound audio.%s loop\n' % FileName)

    # 0x2c
    @log
    def se_fadeout(Duration):  # type: (int) -> None
        s.write(gen_I() + 'stop sound fadeout %.2f\n' % (Duration / 1000.0))

    # 0x29
    @log
    def se_stop():  # type: () -> None
        s.write(gen_I() + 'stop sound\n')

    # 0xc0
    @log
    def play_video(index):  # type:(int) -> None
        # 0: OP, 1: Grand Final ed
        s.write(gen_I() + '$ renpy.movie_cutscene("mov/op.webm")\n')

    # 0x1d
    @log
    def sel_add(Target, Choice):  # type: (str,str) -> None
        s.write(gen_I2(1) + '"%s":\n' % Choice)
        s.write(gen_I2(2) + 'jump %s\n' % Target)

    # 0x1c
    @log
    def sel_beg():  # type: () -> None
        global choice
        choice.clear()
        s.write(gen_I() + 'menu:\n')

    # 0x1b
    @log
    def sel_end():  # type: () -> None
        global choice
        choice.clear()
        s.write('\n')

    # 0x35
    @log
    def yuri(type_):  # type: (int) -> None
        # 1:Up, 2:Down
        global first
        if first:
            s.write(gen_I() + '$yuri = 0\n')
            first = False
        if type_ == 1:
            s.write(gen_I() + '$yuri=yuri+1\n')
        elif type_ == 2:
            s.write(gen_I() + '$yuri=yuri-1\n')

    # 0x05
    @log
    def val_add(index, value):  # type: (int,int) -> None
        s.write(gen_I() + '$var[%s] += %s\n' % (index, value))

    # 0x0d
    @log
    def jmp(Label):  # type: (str) -> None
        s.write(gen_I() + 'jump %s\n' % Label)

    # 0x08
    @log
    def jmp_be(Index, Value, Target):  # type: (int,int,str) -> None
        s.write(gen_I() + 'if var[%s] > %s:\n' % (Index, Value))
        s.write(gen_I2(1) + 'jump %s\n' % Target)

    # 0x06
    @log
    def jmp_eq(Index, Value, Target):  # type: (int,int,str) -> None
        s.write(gen_I() + 'if var[%s] == %s:\n' % (Index, Value))
        s.write(gen_I2(1) + 'jump %s\n' % Target)

    # 0x09
    @log
    def jmp_le(Index, Value, Target):  # type: (int,int,str) -> None
        s.write(gen_I() + 'if var[%s] < %s:\n' % (Index, Value))
        s.write(gen_I2(1) + 'jump %s\n' % Target)

    # 0x2d
    @log
    def se_fadein(index, loop, duration, __, fileName):  # type: (int,int,int,List,str) -> None
        """TODO"""
        se_play(loop, fileName)

    # 0x50
    @log
    def scr_eff(__, additionalCount, distance, duration):  # type: (int,int,int,int) -> None
        # TODO: Difference among shake?
        if __ == 0x00 and additionalCount == 0x01 and distance == 0x10:
            s.write(
                gen_I() + 'with Move((15, 10), (-15, -10), %.2f, bounce=True, repeat=False, delay=.275)\n' % duration)
        elif __ == 0x05 and additionalCount == 0x01 and distance == 0x0c:
            s.write(
                gen_I() + 'with Move((15, 10), (-15, -10), %.2f, bounce=True, repeat=False, delay=.275)\n' % duration)
        elif __ == 0x05 and additionalCount == 0x00 and distance == 0x06:
            s.write(
                gen_I() + 'with Move((15, 10), (-15, -10), %.2f, bounce=True, repeat=False, delay=.275)\n' % duration)

    # 0x51
    @log
    def scr_eff_stop():  # type: () -> None
        # Do Nothing here...
        pass

    @log
    def unknown_0x36(*args):
        pass

    @log
    def unknown_0xba(*args):
        pass

    # 0x21
    @log
    def mark_end(index):  # type: (int) -> None
        """TODO"""

    # 0xb6
    @log
    def dlg_style(style):  # type: (int) -> None
        """Todo"""

    # 0x4d
    @log
    def dlg_fade(visible, duration):  # type: (int,int) -> None
        pass

    # 0x01
    @log
    def exit():  # type: () -> None
        s.write(gen_I() + 'return\n')

    # 0x4c
    @log
    def dlg_clear():  # type: () -> None
        """TODO"""

    # 0x3a
    @log
    def setGoodEndCompleted(index):
        # ZhangHai:
        # Only appeared in Automne and Hiver and only called for normal or good ends.
        # Used by jumpIfHasCompletedEnds() in Hiver.
        """TODO"""

    # 0x3b
    @log
    def jmp_nishuume(Target):  # type: (str) -> None
        # Todo: Just simply jump to label?
        s.write(gen_I() + 'jump %s\n' % Target)

    # 0xb3
    @log
    def play_credits(type_):  # type: (int) -> None
        # 1: True end (Printemps, Ete, Automne) / Good end (Hiver) credits
        # 3: Normal end credits
        """TODO"""

    # 0x83
    @log
    def unknown_0x83(unknown_bytes, unknown_short):  # type: (List[int],int) -> None
        # Always appear after sound play(seplay)
        # Only in Hiver.
        """TODO"""

    # 0x5e
    @log
    def unknown_0x5e(unknown_short):  # type: (int) -> None
        # Only used in 04a_02700s.s. Likely related to selection?
        # Followed by 0x5d, Only equal to 0x00
        """TODO"""

    # 0x5d
    @log
    def unknown_0x5d(unknown_short):  # type: (int) -> None
        # Only used in 04a_02700s.s. Likely related to selection?
        # After 0x5e, Only equal to 0x01
        """TODO"""

    # 0x60
    @log
    def WHAT_THE_FUCK_0x60(l):  # type: (List[int]) -> None
        # Only used in 04a_02700s.s. Likely related to selection?
        """TODO"""

    # 0x60
    @log
    def unknown_0x5f(index, Label):  # type: (int,str) -> None
        # Only used in 04a_02700s.s. Likely related to selection?
        """TODO"""

    # 0x61
    @log
    def unknown_0x61(unknown_byte1, unknown_byte2):  # type: (int,int) -> None
        # Only used in 04a_02700s.s. Likely related to selection?
        # Before 0x8b
        """TODO"""

    # 0x8b
    @log
    def unknown_0x8b(unknown_short):  # type: (int) -> None
        # Only used in 04a_02700s.s. Likely related to selection?
        # Only equal to 0x00
        """TODO"""

    exec(code)

    return S
