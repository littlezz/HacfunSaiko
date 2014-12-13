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





# class Color(bcolors):
#
#     @staticmethod
#     def process(kind: str, value):
#         kind = kind.upper()
#         return getattr(Color, kind) + value +Color.ENDC
#
#     @staticmethod
#     def warning(value):
#         return Color.process('warning', value)
#
#     @staticmethod
#     def okgreen(value):
#         return Color.process('okgreen', value)
#
#     @staticmethod
#     def fail(value):
#         return Color.process('fail', value)
#
#     @staticmethod
#     def header(value):
#         return Color.process('header', value)


# class Prompt:
#
#     input_prompt = """>>> 输入指令和相应的参数,用空格隔开\n"""
#
#     def __init__(self, total=0):
#         self.total = total
#         self.current = 0
#         self.init_texts()
#         self.randomtext()
#         self.error_times = 0
#         self.terminal_size = terminal_width
#
#
#     def prompt(self, func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             ret = func(*args, **kwargs)
#             self._prompt()
#             return ret
#         return wrapper
#
#     @threading_lock(prompt_lock)
#     @clear_output
#     def _prompt(self):
#         self.current += 1
#         print(format(self.current / self.total, '<8.2%') + self.nowtext, end='\r')
#         if self.current % 4 == 0:
#             self.randomtext()
#
#
#     @threading_lock(prompt_detect_error_lock)
#     def _detect_error(self):
#         self.error_times += 1
#
#     def detect_error(self, func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             try:
#                 return func(*args, **kwargs)
#             except Exception as e:
#                 self._detect_error()
#                 raise e
#         return wrapper
#
#     @clear_output
#     def report(self, title):
#         print(format('report', '-^{}'.format(self.terminal_size)))
#         print(title)
#         print('总计{},成功{},失败{}'.format(self.total, self.total - self.error_times, self.error_times))
#         print('-' * self.terminal_size)
#
#
#     def init_texts(self):
#         self.texts = (
#             '正在检查线路安全',
#             '正在确保控制器',
#             '重载思考模型',
#             '正在检查插入栓深度',
#             '正在检查裙子里面的不明突起',
#             '正在解决自涉悖论',
#             '正在展开AT力场',
#             '正在确保线路057',
#             '正在启动过载保护',
#             '魔力控制在预期范围内',
#             '零宽度负预测先行断言 启动',
#             '链式回环加速 启动',
#
#
#         )
#
#     def randomtext(self):
#         self.nowtext = choice(self.texts)
#
#     def reset(self, total, prompt):
#         self.current = 0
#         self.total = total
#         self.error_times = 0
#         print(Color.header(prompt))
#
#     @staticmethod
#     def session_login_ing():
#         print(Color.header('正在验证身份'))
#
#     @staticmethod
#     @clear_output
#     def operate_user_sure(operate, t):
#         print('=' * terminal_width)
#         print('operate: {}'.format(operate))
#         print('args: {}'.format(t))
#
#     @staticmethod
#     def relogin():
#         print(Color.warning('身份验证失败,请登陆'))
#
#     @staticmethod
#     def login_ok():
#         print(Color.okgreen('login success!'))
#
#     @staticmethod
#     def back_commandline():
#         print('返回交互式命令行')
#
#     @staticmethod
#     def not_y_or_N():
#         print('无效的选择')
#
#
#     @staticmethod
#     def list_authors(authors):
#         print_format = '{:<12}| {:<15}| {:<20}'
#         print(print_format.format('作者id', '名字', '添加时间'))
#         for info in authors:
#             print(print_format.format(*info))
#
#     def list_illusts(self, illusts):
#         print_format = '{:<12}| {:<15}| {:<25} | {:<10}'
#         #print(left.format('作者id'), mid.format('作品id'), right.format('名字'))
#         print(print_format.format('作者id', '作品id', '作品名字', '加入时间'))
#         for info in illusts:
#             print(print_format.format(*info))
#
#     def list_update(self, info :list):
#         """
#         :param info: [(author_id, illust_id),]
#         :return:
#         """
#         print('更新内容:')
#         if info:
#             self.list_illusts(info)
#         else:
#             print('没有更新')
#
#     @contextmanager
#     def valid_authorname(self):
#         print('-' * self.terminal_size)
#         print('正在检查id正确性...')
#         yield
#         print('检查完毕')


