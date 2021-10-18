import os
import requests
import argparse
import os.path as path
from colorama import Fore
import urllib
import string
import random
import threading
from progress.bar import ChargingBar

WARNING = f"{Fore.YELLOW}[WARNING]"
RESET = f"{Fore.RESET}"
ERROR = f"{Fore.RED}[ERROR]"
DEBUG = f"{Fore.CYAN}[DEBUG]"
VERBOSE = f"{Fore.LIGHTGREEN_EX}[*]"

parser = argparse.ArgumentParser(description='File Downloader')
parser.add_argument('url', metavar='url', type=str,
                    nargs='+', help="File url to download")
parser.add_argument('-c', '--connections', metavar='N', type=int,
                    nargs=1, help='No. of connections to use')
parser.add_argument('-f', '--file', metavar='<filename>',
                    type=str, nargs=1, help="Save downloaded file as <filename>")
parser.add_argument('-v', '--verbose', action="store_true",
                    help="Get verbose output")
argv = parser.parse_args()

connections = 1
outputfilename = "./temp"
url = ""
response = ""
filelength = 0
verbose = False
if(argv.__getattribute__("verbose")):
    verbose = True
downloadedfile = 0
bar = ChargingBar("Downloading")

# TODO: Implement feature to let user provide/download multiple urls


def fill_url():  # get url from argv
    if argv.__getattribute__("url"):
        url=str(argv.__getattribute__("url")[0])
        url = urllib.parse.unquote(url)
        if argv.__getattribute__("url").__len__() > 1:
            print(
                f"{WARNING}Current we support only one file download, so all urls except '{url}' will be ignored!!{RESET}")
        try:
            if verbose:
                print(
                    f"{VERBOSE}Checking connection to url...{RESET}")
            requests.head(url)
            if verbose:
                print(f"{VERBOSE}Connection successful!{RESET}")
        except requests.ConnectionError as ce:
            print(
                f"{ERROR}Could not connect to {url}, please check the url or the internet.{RESET}")
            exit()
        except requests.exceptions.MissingSchema as missingschema:
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
    else:
        return 1


def fill_file():  # get filename from argv
    try:
        if argv.__getattribute__("file"):
            file = path.abspath(argv.__getattribute__("file")[0])
            if not path.exists(path.dirname(file)):
                raise FileNotFoundError()
        else:
            if verbose:
                print(
                    f"{WARNING}File name not provided, so going with filename from url if possible.{RESET}")

            ret = retrieve_filename(response, url)
            if type(ret) == str:  # try to determine the file extention
                file = ret
                if path.splitext(file)[1]:
                    if verbose:
                        print(
                            f"{VERBOSE}Extention found: {path.splitext(file)[1]} {RESET}")
                else:
                    contenttype = response.headers.get("Content-type")
                    if verbose:
                        print(f"Content: {contenttype}")
                    if contenttype.__contains__("javascript"):
                        file = file + ".js"
                    elif contenttype.__contains__("css"):
                        file = file + ".css"
                    elif contenttype.__contains__("html"):
                        file = file + ".html"
                    elif contenttype.__contains__("zip"):
                        file = file + ".zip"
                if verbose:
                    print(f"{VERBOSE}File name found: {file}{RESET}")
            else:  # Could not retrieve file name from anywhere
                randomname = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=8))
                file = randomname
                if verbose:
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
            contentdispos = str(response.headers.get("Content-Disposition"))
            if contentdispos.__contains__("filename"):
                cdlist = contentdispos.split(";")
                for fn in cdlist:
                    if fn.__contains__("filename"):
                        filekeypair = fn.strip()  # get filename key value pair
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
                        if verbose:
                            print(
                                f"{WARNING}Filename not found in Content-Disposition header.{RESET}")

                return False
            else:
                if verbose:
                    print(
                        f"{WARNING}Filename not found in Content-Disposition header.{RESET}")
                return False
        except IndexError as ie:
            print(
                f"{WARNING}Filename not found in Content-Disposition header.{RESET}")
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
        f"{WARNING}Its seems its '{filetype}' file, you still want to download?{RESET}")
    if not input(f"{WARNING}Enter Y/y to download: ").lower().__contains__("y"):
        print(f"{VERBOSE}Okay Bye!!{RESET}")
        exit()
    else:
        print(RESET, end="")


def calculate_chunk_sizes(connections, filelength):
    remainder = filelength % connections
    filelength -= remainder
    chunksize = int(filelength / connections)
    return chunksize


def server_supports_range(response):
    if not response.headers.get("Accept-Ranges"):
        return False
    else:
        return True


def write_to_file(filename, data):
    with open(filename, 'ab') as f:
        f.write(data)


def report_progress(id, downloadedsize):
    global downloadedfile
    downloadedfile += downloadedsize
    print(VERBOSE)
    bar.next(downloadedsize)
    print(RESET,end="")
    if filelength <= downloadedfile:
        bar.finish()


def download_multipart(url, startrange, finishrange, id, outputfile):
    '''A downloading thread'''
    filename = f"{outputfile}.part{id}"
    chunksizetemp = 1024 * 500
    size = finishrange - startrange
    downloadeddata = 0
    starttemp = 0
    fintemp = 0
    if chunksizetemp > size:
        header = {"Range": f"bytes={startrange}-{finishrange}"}
        content = requests.get(url, headers=header).content
        downloadeddata += content.__len__()
        write_to_file(filename, content)
        report_progress(id, content.__len__())
        if verbose:
            print(
                f"{VERBOSE}Thread({id}) is done!!{Fore.RESET}")
        exit()
    while downloadeddata < size:
        if starttemp == 0 and fintemp == 0:
            starttemp = startrange
            fintemp = starttemp + chunksizetemp
        else:
            starttemp = fintemp + 1
            fintemp = starttemp + chunksizetemp
            if fintemp > finishrange:
                fintemp = finishrange

        header = {"Range": f"bytes={starttemp}-{fintemp}"}

        content = requests.get(url, headers=header).content
        downloadeddata += content.__len__()

        write_to_file(filename, content)
        report_progress(id, content.__len__())
        if path.getsize(filename) >= size:
            # print(
            #     f"{Fore.CYAN}{id}: File size met. f({path.getsize(filename)}) s({size})")
            break
    if verbose:
        print(f"{VERBOSE}{id} is done!!{Fore.RESET}")


def download_singlepart(url, filename):
    filename = f"{filename}.part{id}"
    downloadeddata = 0
    content = requests.get(url).content
    downloadeddata += content.__len__()
    write_to_file(filename, content)
    report_progress(id, content.__len__())
    if verbose:
        print(
            f"{VERBOSE}Thread({id}) is done!!{RESET}")
    exit()


if __name__ == "__main__":
    url = fill_url()
    response = fill_response(url)
    outputfilename = fill_file()
    connections = fill_connections()
    supportsmultipart = True
    try:
        filelength = int(response.headers.get("Content-Length"))
        if filelength < 1025 * 500:
            supportsmultipart = False
    except TypeError as te:
        print(
            f"{WARNING}Server did not tell the file size, so have to use single connection.{RESET}")
        supportsmultipart = False

    if not server_supports_range(response):
        print(f"{WARNING}Sorry, server does not accept ranges{RESET}")
        chunksize = filelength
        supportsmultipart = False
    else:
        chunksize = calculate_chunk_sizes(connections, filelength)

    if verbose:
        print(f"{DEBUG}Connections: {connections},\nURL: {url},\nOutput File: {outputfilename}," +
              f"\nFileLength: {filelength} Bytes{RESET}")
    if not supportsmultipart:
        download_singlepart(url, outputfilename)
    else:
        threaddpool = []
        bar = ChargingBar("Downloading", max=filelength)
        for conn in range(connections):
            if not conn == 0:
                start = (conn * chunksize) + 1
                finish = (start + chunksize) - 1
            else:
                start = 0
                finish = chunksize
            if conn + 1 == connections:
                finish = filelength
            threaddpool.append(threading.Thread(target=download_multipart, args=(
                url, start, finish, conn, outputfilename)))

        print(f"{VERBOSE}Starting...{RESET}")
        try:
            for thread in threaddpool:
                thread.start()
            if verbose:
                print(f"{Fore.LIGHTBLUE_EX}Main: All threads started{Fore.RESET}")
            for thread in threaddpool:
                thread.join()
            bar.finish()
            if verbose:
                print("Main thread free!")
            with open(outputfilename, 'wb') as finalfile:
                for con in range(connections):
                    file = f"{outputfilename}.part{con}"
                    f = open(file, 'rb')
                    for line in f.readlines():
                        finalfile.write(line)
                    f.close()
                    os.remove(file)
            print(f"{VERBOSE} Download complete!!{RESET}")
        except Exception as ex:
            print(ex)
            exit()
