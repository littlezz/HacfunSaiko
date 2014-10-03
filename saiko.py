__author__ = 'zz'


from bs4 import BeautifulSoup
from requests import get
import re

class Analyzer:

    response_pat = re.compile(r'.*?(\d+)')
    div_pat = re.compile(r'threads_')
    def __init__(self, content: bytes, min_response, require_img=False):
        self.html = BeautifulSoup(content)
        self.min_response = min_response
        self.require_img = require_img


    def _parse(self):
        """
        :return: a list of threadsid
        """

        divs = self.html.find_all('div', class_=self.div_pat)

