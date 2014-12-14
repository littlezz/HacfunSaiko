__author__ = 'zz'

from threading import Lock
from random import choice as random_choice
from functools import wraps, partial
from shutil import get_terminal_size
import types

TERMINAL_WIDTH, _ = get_terminal_size()



def clear_output(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(' ' * TERMINAL_WIDTH, end='\r')
        return func(*args, **kwargs)
    return wrapper


class Colors:
    """
     this class is copied from http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


def shellcolor(color: str, func=None):
    """
     Available color:
     header, okblue, okgreen, warning, fail
    """

    if func is None:
        return partial(shellcolor, color)

    color = color.upper()
    color_prefix = getattr(Colors, color, '')
    color_suffix = Colors.ENDC

    @wraps(func)
    def wrapper(*args, **kwargs):
        print(color_prefix, end='')
        ret = func(*args, **kwargs)

        # func use print, there will be a '\n', so must use '\r' write then  back.
        print(color_suffix, end='\r')

        return ret
    return wrapper


class Prompt:

    prompt_text = (
        '正在检查线路安全',
        '正在确保控制器',
        '重载思考模型',
        '正在检查插入栓深度',
        '正在检查裙子里面的不明突起',
        '正在解决自涉悖论',
        '正在展开AT力场',
        '正在确保线路057',
        '正在启动过载保护',
        '魔力控制在预期范围内',
        '零宽度负预测先行断言 启动',
        '链式回环加速 启动',

    )

    def __init__(self, func):
        wraps(func)(self)
        self._lock = Lock()
        self.terminal_width = TERMINAL_WIDTH

        # text which will print
        self._current_text = self._random_text

        # must use self.reset() to set below args
        self._ncalls = 0
        self._total = 0

    @clear_output
    def __call__(self, *args, **kwargs):
        with self._lock:
            self._ncalls += 1
            print(format(self._ncalls / self._total, '<8.2%') + self._current_text, end='\r')

            if self._ncalls % 4 == 0:
                self._current_text = self._random_text

        return self.__wrapped__(*args, **kwargs)

    @property
    def _random_text(self):
        return random_choice(self.prompt_text)

    @shellcolor('header')
    def set_task(self, total, header):
        '''
        total, header
        设置中的任务数, 输出的标题.
        '''
        self._total = total
        self._ncalls = 0
        print(header)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return types.MethodType(self, instance)



