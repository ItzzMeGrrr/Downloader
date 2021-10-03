import requests
import argparse
import os.path as path

from requests import exceptions


parser = argparse.ArgumentParser(description='File Downloader')
parser.add_argument('url', metavar='url', type=str,
                    nargs='+', help="File url to download")
parser.add_argument('-t', '--threads', metavar='N', type=int,
                    nargs=1, help='N no. of threads to use')
parser.add_argument('-f', '--file', metavar='<filename>',
                    type=str, nargs=1, help="Save downloaded file as <filename>")

argv = parser.parse_args()

threads = 1
file = "./temp"
url = argv.__getattribute__("url")[0] #TODO: Implement feature to let user provide/download multiple urls
try:
    urlcheck = requests.head(url)
except requests.ConnectionError as ce:
    print(f"Could not connect to {url}, please check the url")
    exit()
except requests.exceptions.MissingSchema as missingschema:
    print(missingschema)
    exit()
except exceptions as e:
    print(e)
    exit()

if argv.__getattribute__("threads")[0]:
   threads = int(argv.__getattribute__("threads")[0])
try:
    if argv.__getattribute__("file")[0]:
        file = path.abspath(argv.__getattribute__("file")[0])
        if not path.exists(path.dirname(file)):
            raise FileNotFoundError()
        else:
            with open(file,"w") as f:
                pass
        
except FileNotFoundError as fnf:
    print(f"Invalid path: {argv.__getattribute__('file')[0]}")
    exit(1)


        
# downloadfile = ""
# filesize = int(downloadfile.headers.get("Content-Length"))
# if filesize >= 50*1024*1024:
#     print("File bigger than 50MB!!")

# else:
#     print("File smaller than 50MB!!")
