"""exceptions.py"""


class AppException(Exception): """AppException"""


class NetworkError(AppException): """NetworkError"""


class ServerError(AppException): """ServerError"""


class ParserError(AppException): """ParserError"""
