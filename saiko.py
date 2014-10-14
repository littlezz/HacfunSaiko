__author__ = 'zz'


from bs4 import BeautifulSoup
from requests import get as _get
import re
from lib.decorators import retry_connect, sema_lock
import threading
from queue import Queue
from lib.prompt import Prompt
import logging
logging.basicConfig(level=logging.WARNING, format= ' %(message)s')

######################
TIMEOUT = 5
RETRY_TIMES = 3
MAX_THREADINGS = 8
main_host = 'http://h.acfun.tv/%E7%BB%BC%E5%90%88%E7%89%881?page='
#######################


requests_sema = threading.Semaphore(MAX_THREADINGS)
_sentinel = object()
prompt = Prompt()

@retry_connect(RETRY_TIMES, TIMEOUT)
def requests_get(url, **kwargs):
    return _get(url, **kwargs)


class Analyzer:
    host_url = 'http://h.acfun.tv/t/'
    response_pat = re.compile(r'.*?(\d+)')
    div_pat = re.compile(r'threads_')

    def __init__(self, content: bytes, min_response, require_img=False):
        self.html = BeautifulSoup(content)
        self.min_response = min_response
        self.require_img = require_img
        self.parseds = self._parse()

    def _parse(self):
        """
        :return: a iterable of threadsid and blockquote
        """

        divs = self.html.find_all('div', class_=self.div_pat)

        for div in divs:

            if self.require_img and not div.a.img:
                continue

            response_font = div.find('font', color='#707070')
            if response_font:
                response_times =  int(self.response_pat.match(response_font.text).group(1))
                if response_times >= self.min_response:
                    blockquote = div.blockquote.text
                    yield div['class'][0].split('_')[1], blockquote

    @property
    def links(self):
        return (self.host_url + threads_id for threads_id, _ in self.parseds)

    @property
    def infos(self):
        """return iterator (link,blockquote)"""

        return ((self.host_url + threads_id, blockquote) for threads_id, blockquote in self.parseds)


@sema_lock(requests_sema)
@prompt.prompt
def put_content(in_q, url):
    r = requests_get(url)
    in_q.put(r.content)
    logging.debug('url : %s', url)

def parse_contnet(in_q, result, min_res, required_img=False):

    while True:
        content = in_q.get()

        if content is _sentinel:
            break

        result.extend(list(Analyzer(content, min_res, required_img).infos))


def main(start, end, min_res, require_img):
    in_q = Queue(maxsize=10)
    result = []
    _threadings = list()
    prompt.reset(end-start+1,'start')
    for page in range(start, end+1):
        url = main_host + str(page)
        t = threading.Thread(target=put_content, args=(in_q, url))
        t.start()
        _threadings.append(t)



    parse_threading = threading.Thread(target=parse_contnet, args=(in_q, result, min_res, require_img))
    parse_threading.start()

    [t.join() for t in _threadings]
    in_q.put(_sentinel)
    parse_threading.join()

    for info in result:
        print(info[0])
        print(info[1])
        print('-'*70)



if __name__ == '__main__':
    startpage = int(input('start page:\n'))
    endpage = int(input('end page:\n'))
    lowbound =  int(input('the leastest response\n'))
    isrequire = input('require image in the first board? [y/n]\n')
    isrequire = True if isrequire == 'y' else False


    main(startpage, endpage, lowbound, isrequire)
