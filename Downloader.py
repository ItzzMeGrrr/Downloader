import requests
import argparse

parser = argparse.ArgumentParser(description='File Downloader')
parser.add_argument('url', metavar='url', type=str,
                    nargs='+', help="File url to download")
parser.add_argument('-t', '--threads', metavar='N', type=int,
                    nargs=1, help='N no. of threads to use')
parser.add_argument('-f', '--file', metavar='<filename>',
                    type=str, nargs=1, help="Save downloaded file as <filename>")

argv = parser.parse_args()

print(argv.__getattribute__("url")[0])
# downloadfile = ""
# filesize = int(downloadfile.headers.get("Content-Length"))
# if filesize >= 50*1024*1024:
#     print("File bigger than 50MB!!")

# else:
#     print("File smaller than 50MB!!")
