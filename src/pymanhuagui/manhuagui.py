"""manhuagui.py"""
import logging
import re
import json
import shutil

from dataclasses import dataclass
from typing import List

import requests
import bs4
import lzstring
import js2py

from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter

from .exceptions import NetworkError, ServerError, ParserError


BASE_URL = 'https://www.manhuagui.com'
IMG_BASE_URL = 'https://i.hamreus.com'
MAX_RETRIES = 5
POOL_SIZE = 1


@dataclass
class BookEntry:
    """BookEntry"""
    id: str
    url: str


@dataclass
class VolumeData:
    """VolumeData"""
    url: str
    id: str
    title: str
    page_qty: int
    section: str


@dataclass
class BookData:
    """BookData"""
    url: str
    id: str
    name: str = None
    cover: str = None
    original_name: str = None
    aliases: List[str] = None
    description: str = None
    production_year: int = None
    location: str = None
    genres: List[str] = None
    last_updated: str = None
    is_complete: bool = None
    authors: List[str] = None
    volume_qty: int = None
    volumes: List[VolumeData] = None

    @classmethod
    def create(cls, book_entry: BookEntry):
        """create()"""
        return cls(book_entry.url, book_entry.id)



http = requests.Session()
http.mount('https://', HTTPAdapter(max_retries=MAX_RETRIES,
                                   pool_connections=POOL_SIZE,
                                   pool_maxsize=POOL_SIZE))


logger = logging.getLogger(__name__)


def _eval(function, default=None):
    """_eval()"""
    try:
        return function()
    except BaseException:
        return default


def _request(url):
    """_request()"""
    logger.info('Fetch %s', url)

    try:
        return http.get(url, headers={
            'Accept-Language': 'zh-CN'
        })
    except RequestException as exc:
        logger.error('Failed to get %s', url)
        raise NetworkError from exc


def _parse_volumes(html_entity: bs4.BeautifulSoup):
    """_parse_volumes()"""
    volumes = []
    volume_section = ''

    for element in html_entity.find(attrs={'class': 'chapter'}):
        if element.name == 'h4':
            volume_section = element.text
        elif element.name == 'div' and \
            'class' in element.attrs and 'chapter-list' in element.attrs['class']:
            for ul in element.find_all('ul'):
                anchors = ul.find_all('a')
                for anchor in reversed(anchors):
                    volume_entry_path = anchor.attrs["href"]
                    volumes.append(VolumeData(
                        BASE_URL + volume_entry_path,
                        volume_entry_path[volume_entry_path.rfind('/') + 1:-5],
                        anchor.attrs["title"],
                        int(anchor.find('i').text[:-1]),
                        volume_section
                    ))
        elif element.name == 'input' and element.attrs['id'] == '__VIEWSTATE':
            html_part = '<div class="chapter">%s</div>' % \
                lzstring.LZString.decompressFromBase64(element.attrs['value'])
            return _parse_volumes(bs4.BeautifulSoup(html_part, features='lxml'))
    return volumes


def parse_entry_url(entry_url) -> BookEntry:
    """parse_entry_url()"""
    result = re.match(r'^https:\/\/(www|m)\.manhuagui\.com\/comic\/(\d+)\/', entry_url, re.I)
    if result is None:
        raise ValueError
    book_url = result.group(0)
    book_id = result.group(2)
    if result.group(1) == 'm':
        book_url = 'https://www' + book_url[len('https://m'):]
    return BookEntry(book_id, book_url)


def fetch_book(book_entry: BookEntry):
    """fetch_book()"""
    book_data = BookData.create(book_entry)
    response = _request(book_entry.url)
    if not response.ok:
        raise ServerError(response)

    try:
        html_entity = bs4.BeautifulSoup(response.content, features='lxml')
        book_data.volumes = _parse_volumes(html_entity)
        book_data.volume_qty = len(book_data.volumes)
        book_title_div = html_entity.find(attrs={'class': 'book-title'})
        book_data.name = book_title_div.findChild('h1').text
        subtitle = book_title_div.findChild('h2').text
        if subtitle:
            book_data.alias = [subtitle]
        book_data.description = '\n'.join([_p.text for _p in html_entity.find(attrs={'id': 'intro-all'}).findChildren('p')])
        book_data.cover = 'https:' + html_entity.find('p', attrs={'class': 'hcover'}).findChild('img').attrs['src']
        book_detail_list = html_entity.find('ul', attrs={'class': 'detail-list'})
        for span in book_detail_list.select('li>span'):
            label_name = span.findChild('strong').text
            if label_name == '出品年代：':
                book_data.production_year = _eval(lambda: span.findChild('a').text[:-1])
            elif label_name == '漫画地区：':
                book_data.location = _eval(lambda: span.findChild('a').text)
            elif label_name == '漫画剧情：':
                book_data.genres = _eval(lambda: [_.text for _ in span.findChildren('a')])
            elif label_name == '漫画作者：':
                book_data.authors = _eval(lambda: [_.text for _ in span.findChildren('a')])
            elif label_name == '漫画别名：':
                book_data.aliases = _eval(lambda: [_.text for _ in span.findChildren('a')])
            elif label_name == '漫画状态：':
                book_data.is_complete = _eval(lambda: span.findChild('span').text == '已完结')
                book_data.last_updated = _eval(lambda: span.findChildren('span')[1].text)
    except Exception as exc:
        raise ParserError from exc

    return book_data


def fetch_volume(volume: VolumeData):
    """fetch_volume()"""
    response = _request(volume.url)
    if not response.ok:
        raise ServerError(response)

    try:
        js_code = re.search(
            r'<script type="text\/javascript">window\["\\x65\\x76\\x61\\x6c"\](\(function\(p.*?)</script>', 
            response.content.decode('utf-8')
        ).group(1)
        js_ctx = js2py.EvalJs({
            'decompressFromBase64': lambda s: lzstring.LZString.decompressFromBase64(s.value)
        })
        js_ctx.execute('String.prototype.splic=function(f){return decompressFromBase64(this).split(f)};')
        json_content = re.search(r"(\{.*\})", js_ctx.eval(js_code)).group(1)
        img_data = json.loads(json_content)
        img_query = '?e={e}&m={m}'.format(e=img_data['sl']['e'], m=img_data['sl']['m'])
        img_url = IMG_BASE_URL + img_data['path']
        return [img_url + f + img_query for i, f in enumerate(img_data['files'])]
    except Exception as exc:
        raise ParserError from exc


def download(url, save_path):
    """download()"""
    logger.info('download %s, save to %s', url, save_path)

    try:
        response = http.get(url, stream=True, headers={
            'Accept-Language': 'zh-CN',
            'Referer': BASE_URL,
        })
    except RequestException as exc:
        logger.error('Failed to download %s', url)
        raise NetworkError from exc

    if not response.ok:
        raise ServerError(response)

    with open(save_path, 'wb') as f:
        response.raw.decode_content = True
        shutil.copyfileobj(response.raw, f)

    response.close()
