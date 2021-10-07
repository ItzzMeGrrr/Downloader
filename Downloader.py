import os
import requests
import argparse
import urllib.parse
import os.path as path
from colorama import Fore
from requests import exceptions
import string
import random

from requests.models import Response


WARNING = f"{Fore.YELLOW}[!]"
RESET = f"{Fore.RESET}"
ERROR = f"{Fore.RED}[⨂ ]"
DEBUG = f"{Fore.CYAN}[ ⁓ ]"
POSITIVE = f"{Fore.LIGHTGREEN_EX}[*]"

parser = argparse.ArgumentParser(description='File Downloader')
parser.add_argument('url', metavar='url', type=str,
                    nargs='+', help="File url to download")
parser.add_argument('-c', '--connections', metavar='N', type=int,
                    nargs=1, help='N no. of connections to use')
parser.add_argument('-f', '--file', metavar='<filename>',
                    type=str, nargs=1, help="Save downloaded file as <filename>")
argv = parser.parse_args()

connections = 1
file = "./temp"
url = ""
response = ""
filelength = 0


# TODO: Implement feature to let user provide/download multiple urls
def fill_url():  # get url from argv
    if argv.__getattribute__("url"):
        url = str(argv.__getattribute__("url")[0])
        if argv.__getattribute__("url").__len__() > 1:
            print(
                f"{WARNING}Current we support only one file download, so all urls except '{url}' will be ignored!!{RESET}")
        try:
            print(
                f"{POSITIVE}Checking connection to url...{RESET}")
            requests.head(url)
            print(f"{POSITIVE}Connection successful!{RESET}")
        except requests.ConnectionError as ce:
            print(
                f"{ERROR}Could not connect to {url}, please check the url or the internet.{RESET}")
            exit()
        except exceptions.MissingSchema as missingschema:
            print(f"{ERROR}" +
                  str(missingschema)+f"{RESET}")
            exit()
        except Exception as e:
            print(e)
            exit()
    else:
        print(f"{ERROR}URL not found!!{RESET}")
        exit()
    return url


def fill_connections():  # get connections from argv
    if argv.__getattribute__("connections"):
        connections = int(argv.__getattribute__("connections")[0])
        return connections


def fill_file():  # get filename from argv
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
                f"{WARNING}File name not provided, so going with filename from url if possible.{RESET}")

            ret = retrieve_filename(response, url)
            if type(ret) == str:
                file = ret
                if path.splitext(file)[1]:
                    print("Extention found")
                else:
                    contenttype = response.headers.get("Content-type")
                    print(f"Content: {contenttype}")
                    if contenttype.__contains__("javascript"):
                        file = file + ".js"
                    elif contenttype.__contains__("css"):
                        file = file + ".css"
                    elif contenttype.__contains__("html"):
                        file = file + ".html"
                    elif contenttype.__contains__("zip"):
                        file = file + ".zip"                    
                    
                print(f"{POSITIVE}File name found: {file}{RESET}")
            else:
                randomname = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=8))
                file = randomname

                print(
                    f"{WARNING}Could not determine filename so going random.{RESET}")

    except FileNotFoundError as fnf:
        print(
            f"{ERROR}Invalid path: {argv.__getattribute__('file')[0]}{RESET}")
        exit(1)
    return file


def retrieve_filename(response, url):
    tempurl = urllib.parse.urlparse(url)
    tempfilename = path.basename(tempurl.path)
    if tempfilename:
        return tempfilename
    else:
        try:
            contentdispos = response.headers.get("Content-Disposition")
            if(contentdispos):
                cdlist = contentdispos.split(";")  # remove 'attachment' prefix
                filekeypair = cdlist[1].strip()  # get filename key value pair
                filenameraw = filekeypair.split(
                    "=")[1]  # remove 'filename' prefix
                # check if double quotes are present
                if filenameraw.__contains__("\""):
                    filenameprocessed = filenameraw.replace(
                        "\"", "", 2)  # remove double quotes
                    return filenameprocessed
                else:
                    return filenameraw
            else:
                return False
        except IndexError as ie:
            print(
                f"{WARNING}filename not found in Content-Disposition header.{RESET}")
            return False


def fill_response(url):
    resp = requests.head(url, allow_redirects=True)
    contenttype = resp.headers.get("Content-type")

    if contenttype.__contains__("javascript"):
        still_download("JavaScript")
    elif contenttype.__contains__("css"):
        still_download("CSS")
    elif contenttype.__contains__("html"):
        still_download("HTML")
    elif contenttype.__contains__("text"):
        still_download(contenttype.split("/")[1])
    
    return resp


def still_download(filetype):
    print(
        f"{WARNING}Its seems its {filetype} file, you still want to download?{RESET}")
    if not input(f"{WARNING}Enter Y/y to download: ").lower().__contains__("y"):
        print(f"{POSITIVE}Okay Bye!!{RESET}")
        exit()
    else:
        print(RESET, end="")


if __name__ == "__main__":
    url = fill_url()
    response = fill_response(url)
    file = fill_file()
    connections = fill_connections()
    filelength = response.headers.get("Content-length")
    print(f"{DEBUG}Connections: {connections},\nURL: {url},\nOutput File: {file},\nFileLength: {filelength} Bytes {RESET}")
