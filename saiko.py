import queue
import re
import threading
from lib.decorators import loop, retry_connect
import requests
from bs4 import BeautifulSoup
from lib.prompt import Prompt
import logging
logging.basicConfig(level=logging.WARNING, format=' %(message)s')
__author__ = 'zz'


### config #########
TIMEOUT = 3
RETRY_TIMES = 3
MAX_THREADING = 4
HOST = 'http://h.acfun.tv/%E7%BB%BC%E5%90%88%E7%89%881?page='
#######################


class AsyncRequest(requests.Session):
    def __init__(self, max_threading=4):
        self.max_threading = max_threading
        self._lock = threading.Lock()
        self._in_q = queue.Queue()
        self._out_q = queue.Queue()
        self.sentinel = object()
        self._threading_exit_num = 0

        super().__init__()

    def submit(self, url):
        self._in_q.put(url)

    @retry_connect(retry_times=RETRY_TIMES, timeout=TIMEOUT)
    def get(self, url, **kwargs):
        return super().get(url, **kwargs)

    @loop
    def _threading_process(self):
        url = self._in_q.get()

        if url == self.sentinel:
            self._in_q.put(self.sentinel)
            self._threading_exit_signal()
            return True

        resp = self.get(url)
        self._out_q.put(resp.content)

        #call prompt
        self.prompt()

    def _threading_exit_signal(self):
        """统计结束的线程, 全部退出后给出口队列提交self.sentinel"""
        self._threading_exit_num += 1

        # all threading were exited
        if self._threading_exit_num == self.max_threading - 1:
            self._out_q.put(self.sentinel)

    def stop(self):
        self._in_q.put(self.sentinel)

    def start(self):
        for i in range(self.max_threading):
            t = threading.Thread(target=self._threading_process)
            t.start()

    def extract(self):
        """when every threading had been exied return self.sentinel
        else return resp.content"""
        return self._out_q.get()

    @Prompt
    def prompt(self):
        """
        do nothing
        when process execute, call this method for Prompt to count.
        """
        pass


class Analyzer:
    host_url = 'http://h.acfun.tv/t/'
    response_pat = re.compile(r'.*?(\d+)')
    main_div = 'h-threads-item uk-clearfix'

    def __init__(self, min_response, required_img=False):
        self._results = []
        self.min_response = min_response
        self.required_img = required_img

    @property
    def results(self):
        """
        :return: yield result
        """
        for result in self._results:
            yield result

    @staticmethod
    def _bs_find_response(tag):
        """
        验证是否有大于多少条回复的那句话, 应为sega和这个是同一个css class, 所以特别使用一个func来验证

        """
        #FIXME: [] waste time!
        if tag.has_attr('class') and tag['class'] == ['h-threads-tips']:
            return True
        else:
            return False

    def analyze(self, content: bytes):
        """analyze the resp.content, put (link, blockquote) to self._result
        """
        bs = BeautifulSoup(content)
        divs = bs.find_all('div', class_=self.main_div)

        for div in divs:
            # find img box
            if self.required_img and \
                    not div.find('div', class_='h-threads-item-main').find('div', class_='h-threads-img-box'):

                continue

            response_div = div.find(self._bs_find_response)

            if response_div:

                response_tot = int(self.response_pat.match(response_div.text).group(1))
                if response_tot >= self.min_response:

                    blockquote = div.find('div', class_='h-threads-content').text
                    link = self.host_url + div['data-threads-id']

                    self._results.append((link, blockquote))


class IntDescriptor:
    def __init__(self, name):
        self.name = name

    def __set__(self, instance, value):
        value = int(value)
        instance.__dict__[self.name] = value


class UserInput:
    start = IntDescriptor('start')
    end = IntDescriptor('end')
    min_response = IntDescriptor('min_response')

    def __init__(self):
        self.required_img = False

    @loop
    def collect(self):
        try:
            self.start = input('input the start page(default 1)\n') or '1'
            self.end = input('end page\n')
            self.min_response = input('min response? \n')
            self.required_img = True if input('require img? [y/n]\n') == 'y' else False

        except ValueError:
            self.raise_errorinfo()
            return False

        if self.start >= self.end:
            self.raise_errorinfo()
            return False

        return True

    @staticmethod
    def raise_errorinfo():
        print('Unvalid value, please input again.\n')


@loop
def analyze_content(analyzer: Analyzer, async_request: AsyncRequest):
    content = async_request.extract()

    if content == async_request.sentinel:
        return True

    analyzer.analyze(content)


def main():
    user_input = UserInput()
    user_input.collect()

    async_request = AsyncRequest(max_threading=4)
    async_request.start()

    logging.debug('start: %s, end: %s, min: %s, img?: %s',
                  user_input.start, user_input.end, user_input.min_response, user_input.required_img)

    async_request.prompt.set_task(user_input.end - user_input.start + 1, '开始下载')

    for pn in range(user_input.start, user_input.end + 1):
        request_url = HOST + str(pn)
        async_request.submit(request_url)

    # there is no more info to put to async_requests.
    async_request.stop()

    analyzer = Analyzer(min_response=user_input.min_response)

    analyze_content(analyzer, async_request)
    for link, blockquote in analyzer.results:
        print(link)
        print(blockquote)
        print('-' * 70)


if __name__ == '__main__':
    main()
