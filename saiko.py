import queue
import re
import threading
from lib.decorators import loop, retry_connect
import requests
from bs4 import BeautifulSoup
__author__ = 'zz'


### config #########
TIMEOUT = 3
RETRY_TIMES = 3
MAX_THREADING = 4
#######################


class AsyncRequest(requests.Session):
    def __init__(self, max_threading=4):
        self.max_threading = max_threading
        self._lock = threading.Lock()
        self._in_q = queue.Queue()
        self._out_q = queue.Queue()
        self._sentinel = object()
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

        if url == self._sentinel:
            self._in_q.put(self._sentinel)
            self._threading_exit_signal()
            return True

        resp = self.get(url)
        self._out_q.put(resp.content)

    def _threading_exit_signal(self):
        """统计结束的线程, 全部退出后给出口队列提交self._sentinel"""
        self._threading_exit_num += 1

        # all threading were exited
        if self._threading_exit_num == self.max_threading - 1:
            self._out_q.put(self._sentinel)

    def stop(self):
        self._in_q.put(self._sentinel)

    def start(self):
        for i in range(self.max_threading):
            t = threading.Thread(target=self._threading_process)
            t.start()

    def extract(self):
        """when every threading had been exied return self._sentinel
        else return resp.content"""
        return self._out_q.get()


class Analyzer:
    host_url = 'http://h.acfun.tv/t/'
    response_pat = re.compile(r'.*?(\d+)')
    main_div = 'h-threads-item uk-clearfix'

    def __int__(self, min_response, required_img=False):
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

            response_div = bs.find(self._bs_find_response)

            if response_div:
                response_tot = int(self.response_pat.match(response_div.text).group(1))
                if response_tot >= self.min_response:

                    blockquote = div.find('div',class_='h-threads-content').text
                    link = self.host_url + div['data-threads-id']

                    self._results.append((link, blockquote))


