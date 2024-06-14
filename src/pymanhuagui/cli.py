"""cli.py"""
import sys
import argparse
import importlib.metadata


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
