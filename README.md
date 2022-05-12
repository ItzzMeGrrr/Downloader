# Downloader
File downloader in python. It creates given no. of connections and downloads files in parallel.

### Usage
```
usage: Downloader.py [-h] [-c N] [-f <filename>] [-v] url [url ...]

File Downloader

positional arguments:
  url                   File url to download

optional arguments:
  -h, --help            show this help message and exit
  -c N, --connections N
                        No. of connections to use
  -f <filename>, --file <filename>
                        Save downloaded file as
  -v, --verbose         Get verbose output
```