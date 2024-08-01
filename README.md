# PyManhuagui

[漫画柜](https://www.manhuagui.com)下载工具。

安装：

```sh
pip install pymanhuagui
```

用法：

```text
usage: pymanhuagui [-o dir] [-x host] [-s name] [-d] [-v] [-h] url

Manga Downloader for www.manhuagui.com

positional arguments:
  url                   manga url, e.g., https://www.manhuagui.com/comic/1639/

optional arguments:
  -o dir, --output dir  write stdout to the specified file
  -x host, --proxy host
                        use proxy server
  -s name, --section name
                        one or more section names to be downloaded
  -d, --debug           display debug message
  -v, --version         show program's version number and exit
  -h, --help            show this help message and exit
```

例子：

```shell
pymanhuagui -s 完全版 -s 全彩版 https://www.manhuagui.com/comic/1639/
```
