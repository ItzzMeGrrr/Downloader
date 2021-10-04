import requests
import argparse
import urllib.parse
import os.path as path
from colorama import Fore
from requests import exceptions
import string
import random


def retrievefilename(response, url):
    tempurl = urllib.parse.urlparse(url)
    tempfilename = path.basename(tempurl.path)
    if tempfilename:
        return tempfilename

    contentdispos = response.headers.get("Content-Disposition")
    if(contentdispos):
        cdlist = contentdispos.split(";")  # remove 'attachment' prefix
        filekeypair = cdlist[1].strip()  # get filename key value pair
        filenameraw = filekeypair.split("=")[1]  # remove 'filename' prefix
        # check if double quotes are present
        if filenameraw.__contains__("\""):
            filenameprocessed = filenameraw.replace(
                "\"", "", 2)  # remove double quotes
        return filenameprocessed
    else:
        return False


def retrievefiletype(response):
    contenttype = response.headers.get("Content-type")



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
url = ""
# get url from argv
# TODO: Implement feature to let user provide/download multiple urls
if argv.__getattribute__("url"):
    url = argv.__getattribute__("url")[0]
    if argv.__getattribute__("url").__len__() > 1:
        print(
            f"{Fore.YELLOW}[*] Current we support only one file download, so all urls except '{url}' will be ignored!!{Fore.RESET}")
    try:
        print(
            f"{Fore.LIGHTGREEN_EX}[*]Checking connection to url...{Fore.RESET}")
        response = requests.head(url)
        print(f"{Fore.LIGHTGREEN_EX}[*]Connection successful!{Fore.RESET}")
    except requests.ConnectionError as ce:
        print(
            f"{Fore.RED}[!]Could not connect to {url}, please check the url.{Fore.RESET}")
        exit()
    except exceptions.MissingSchema as missingschema:
        print(f"{Fore.RED}[!]" +
              str(missingschema)+f"{Fore.RESET}")
        exit()
    except Exception as e:
        print(e)
        exit()
else:
    print(f"{Fore.RED}[!]URL not found!!{Fore.RESET}")
    exit()

# get threads from argv
if argv.__getattribute__("threads"):
    threads = int(argv.__getattribute__("threads")[0])

# get filename from argv
try:
    if argv.__getattribute__("file"):
        file = path.abspath(argv.__getattribute__("file")[0])
        if not path.exists(path.dirname(file)):
            raise FileNotFoundError()
        else:
            with open(file, "w") as f:
                pass

    else:
        print(
            f"{Fore.YELLOW}[*]File name not provided, so going with filename from url if possible.{Fore.RESET}")

        ret = retrievefilename(response, url)
        if type(ret).__eq__(str):
            file = ret
        else:
            randomname = ''.join(random.choices(
                string.ascii_letters + string.digits, k=8))
            filetype = retrievefiletype(response)
            if type(filetype).__eq__(str):
                randomname.join("." + filetype)

            print(
                f"{Fore.YELLOW}[*]Could not determine filename so going random.{Fore.RESET}")


except FileNotFoundError as fnf:
    print(
        f"{Fore.RED}[!]Invalid path: {argv.__getattribute__('file')[0]}{Fore.RESET}")
    exit(1)
except Exception as exc:
    print(exc)
    exit()


# filesize = int(downloadfile.headers.get("Content-Length"))
# if filesize >= 10*1024*1024:
#     print("File bigger than 10MB!!")
# else:
#     print("File smaller than 10MB!!")
