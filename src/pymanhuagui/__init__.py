"""__init__.py"""
import logging
import os
import sys

from urllib.parse import urlparse

from .cli import parse_args
from .manhuagui import parse_entry_url, fetch_book, fetch_volume, download


logger = logging.getLogger(__name__)


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
        logger.error('Illegal url: %s', args.url)
        return -1

    output_dir = os.path.realpath(args.output) if args.output else os.getcwd()
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    elif os.path.isfile(output_dir):
        logger.error('Output path "%s" is a file', output_dir)
        return -1

    book_data = fetch_book(book_entry)
    book_save_path = os.path.join(output_dir, book_data.name)
    if not os.path.exists(book_save_path):
        os.makedirs(book_save_path)
    cover_save_path = os.path.join(
        book_save_path,
        'cover' + os.path.splitext(urlparse(book_data.cover).path)[1]    
    )
    if not os.path.exists(cover_save_path):
        download(book_data.cover, cover_save_path)
    for volume_data in book_data.volumes:
        volume_save_path = os.path.join(book_save_path, volume_data.title)
        if not os.path.exists(volume_save_path):
            os.makedirs(volume_save_path)
        for page_data in fetch_volume(volume_data):
            page_save_path = os.path.join(
                volume_save_path,
                str(page_data.number).zfill(len(str(volume_data.page_qty))) + \
                    os.path.splitext(urlparse(page_data.url).path)[1]
            )
            if not os.path.exists(page_save_path):
                download(page_data.url, page_save_path)

    return 0


def handle_exception(exc_type, exc, tb):
    """handle_exception()"""
    logger.error('An uncaught error occurred: [%s] %s', exc_type.__name__, exc)
    sys.exit(-1)


sys.excepthook = handle_exception
