"""cli.py"""
import logging
import os
import re
import sys
import argparse
import importlib.metadata

from urllib.parse import urlparse

from .manhuagui import parse_entry_url, fetch_book, fetch_volume, download


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """parse_args()"""
    pkg_meta = importlib.metadata.metadata(__package__)
    pkg_version = pkg_meta['Version']
    pkg_name = pkg_meta['Name']
    pkg_description = pkg_meta['Summary']

    parser = argparse.ArgumentParser(
        prog = pkg_name,
        description = pkg_description,
        add_help=False
    )

    parser.add_argument('url', help='manga url, e.g., https://www.manhuagui.com/comic/1639/')
    parser.add_argument('-o', '--output', metavar='dir', dest='output',
                        help='write stdout to the specified file')
    parser.add_argument('-x', '--proxy', metavar='host', dest='proxy',
                        help='use proxy server')
    parser.add_argument('-d', '--debug', action='store_true', help='display debug message')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + pkg_version)
    parser.add_argument('-h', '--help', action='help', help='show this help message and exit')

    return parser.parse_args(sys.argv[1:])


def main() -> int:
    """main()"""
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

    try:
        book_entry = parse_entry_url(args.url)
    except ValueError:
        logger.error('Invalid book url: %s', args.url)
        return -1

    output_dir = os.path.abspath(args.output) if args.output else os.getcwd()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.debug('Path "%s" created', output_dir)
    elif os.path.isfile(output_dir):
        logger.error('Output path "%s" is not a directory', output_dir)
        return -1
    else:
        logger.debug('Output path "%s" already exists', output_dir)

    if args.proxy:
        os.environ['HTTP_PROXY'] = args.proxy
        os.environ['HTTPS_PROXY'] = args.proxy
        logger.info('Using proxy %s', args.proxy)

    filename_replacement = re.compile(r'[\\\/\:\<\>\"\|\?\*]')
    def make_filename(name:str) -> str:
        return filename_replacement.sub('-', name).strip(' .-')

    book_data = fetch_book(book_entry)
    book_save_path = os.path.join(output_dir, make_filename(book_data.name))
    if not os.path.exists(book_save_path):
        os.makedirs(book_save_path)
        logger.debug('Path "%s" created', book_save_path)
    else:
        logger.debug('Book save path "%s" already exists', book_save_path)

    cover_save_path = os.path.join(
        book_save_path,
        'cover' + os.path.splitext(urlparse(book_data.cover).path)[1]    
    )
    if not os.path.exists(cover_save_path):
        download(book_data.cover, cover_save_path)
    else:
        logger.debug('Book cover "%s" already exists', cover_save_path)

    readme_path = os.path.join(book_save_path, 'README.txt')
    with open(readme_path, 'w', encoding='UTF-8') as readme:
        readme.writelines((
            f"《{book_data.name}》（{'已完结' if book_data.is_complete else '未完结'}）\n",
            book_data.url,
            '\n',
            '\n',
            f"作者：\t\t{'、'.join(book_data.authors)}\n",
            f"分类：\t\t{'、'.join(book_data.genres)}\n",
            f"地区：\t\t{book_data.location}\n",
            f"出品年份：\t{book_data.production_year}\n",
            f"最后更新：\t{book_data.last_updated}\n",
            '简介：\n',
            book_data.description,
        ))

    volumes_len = len(book_data.volumes)
    if volumes_len > 0:
        logger.info('%d volume(s) fetched', volumes_len)
    else:
        logger.error('Unable to fetch volume info, the book may have been removed')

    for volume_data in book_data.volumes:
        volume_save_path = os.path.join(book_save_path, make_filename(volume_data.title))
        if not os.path.exists(volume_save_path):
            os.makedirs(volume_save_path)
            logger.debug('Path "%s" created', volume_save_path)
        else:
            logger.debug('Volume save path "%s" already exists', volume_save_path)
        for page_index, page_url in enumerate(fetch_volume(volume_data)):
            page_save_path = os.path.join(
                volume_save_path,
                str(page_index + 1).zfill(len(str(volume_data.page_qty))) + \
                    os.path.splitext(urlparse(page_url).path)[1]
            )
            if not os.path.exists(page_save_path):
                download(page_url, page_save_path)
            else:
                logger.debug('Page "%s" already exists', page_save_path)

    logger.info('All done.')
    return 0
