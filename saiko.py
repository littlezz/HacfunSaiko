import queue
import threading
from lib.decorators import loop, retry_connect
import requests
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
        return self._out_q.get()





