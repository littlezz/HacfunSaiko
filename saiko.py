__author__ = 'zz'


from bs4 import BeautifulSoup
from requests import get
import re

class Analyzer:

    host_url = 'http://h.acfun.tv/t/'
    response_pat = re.compile(r'.*?(\d+)')
    div_pat = re.compile(r'threads_')



    def __init__(self, content: bytes, min_response, require_img=False):
        self.html = BeautifulSoup(content)
        self.min_response = str(min_response)
        self.require_img = require_img


    def _parse(self):
        """
        :return: a list of threadsid
        """

        divs = self.html.find_all('div', class_=self.div_pat)

        for div in divs:

            if self.require_img and not div.a.img:
                continue

            response_font = div.find('font', color='#707070')
            if response_font:
                response_times =  self.response_pat.match(response_font.text).group(1)
                if response_times >= self.min_response:
                    yield div['class'][0].split('_')[1]

    @property
    def links(self):
        return  (self.host_url + threads_id for threads_id in self._parse())
