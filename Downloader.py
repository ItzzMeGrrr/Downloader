import os
import sys
import requests
import argparse
import os.path as path
from colorama import Fore
import urllib
import string
import random
import threading
from progress.bar import ChargingBar
from socket import gaierror
from urllib3.exceptions import NewConnectionError

COLOR_WARNING = f"{Fore.YELLOW}[WARNING]"
COLOR_RESET = f"{Fore.RESET}"
COLOR_ERROR = f"{Fore.RED}[ERROR]"
COLOR_DEBUG = f"{Fore.CYAN}[DEBUG]"
COLOR_VERBOSE = f"{Fore.LIGHTGREEN_EX}[*]"

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


def fill_url():
    '''Returns url from argv'''
    if argv.__getattribute__("url"):
        url = str(argv.__getattribute__("url")[0])
        url = urllib.parse.unquote(url)
        if argv.__getattribute__("url").__len__() > 1:
            print(
                f"{COLOR_WARNING}Current we support only one file download, so all urls except '{url}' will be ignored!!{COLOR_RESET}")
        try:
            if verbose:
                print(
                    f"\r{COLOR_VERBOSE}Checking connection to url...{COLOR_RESET}")
            requests.head(url)
            if verbose:
                print(f"\r{COLOR_VERBOSE}Connection successful!{COLOR_RESET}")
        except requests.ConnectionError as ce:
            print(
                f"{COLOR_ERROR}Could not connect to {url}, please check the url or the internet.{COLOR_RESET}")
            exit()
        except requests.exceptions.MissingSchema as missingschema:
            print(f"{COLOR_ERROR}" +
                  str(missingschema)+f"{COLOR_RESET}")
            exit()
        except Exception as e:
            print(e)
            exit()
    else:
        print(f"{COLOR_ERROR}URL not found!!{COLOR_RESET}")
        exit()
    return url


def fill_connections():
    '''Returns connections from argv'''
    if argv.__getattribute__("connections"):
        connections = int(argv.__getattribute__("connections")[0])
        return connections
    else:
        return 1


def fill_file():
    '''Returns filename from argv'''
    try:
        if argv.__getattribute__("file"):
            file = path.abspath(argv.__getattribute__("file")[0])
            if not path.exists(path.dirname(file)):
                raise FileNotFoundError()
        else:
            if verbose:
                print(
                    f"\r{COLOR_WARNING}File name not provided, so going with filename from url if possible.{COLOR_RESET}")

            ret = retrieve_filename(response, url)
            if type(ret) == str:  # try to determine the file extention
                file = ret
                if path.splitext(file)[1]:
                    pass
                else:
                    contenttype = response.headers.get("Content-type")
                    if contenttype.__contains__("javascript"):
                        file = file + ".js"
                    elif contenttype.__contains__("css"):
                        file = file + ".css"
                    elif contenttype.__contains__("html"):
                        file = file + ".html"
                    elif contenttype.__contains__("zip"):
                        file = file + ".zip"
                if verbose:
                    print(
                        f"\r{COLOR_VERBOSE}File name found: {file}{COLOR_RESET}\n")
            else:  # Could not retrieve file name from anywhere
                randomname = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=8))
                file = randomname
                if verbose:
                    print(
                        f"\r{COLOR_WARNING}Could not determine filename so going random.{COLOR_RESET}\n")

    except FileNotFoundError as fnf:
        print(
            f"{COLOR_ERROR}Invalid path: {argv.__getattribute__('file')[0]}{COLOR_RESET}")
        exit(1)
    return file


def retrieve_filename(response, url):
    '''Tries retrieve filename from url or Content-Disposition header othrewise generates random filename'''
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
                                f"\r{COLOR_WARNING}Filename not found in Content-Disposition header.{COLOR_RESET}\n")

                return False
            else:
                if verbose:
                    print(
                        f"\r{COLOR_WARNING}Filename not found in Content-Disposition header.{COLOR_RESET}\n")
                return False
        except IndexError as ie:
            print(
                f"{COLOR_WARNING}Filename not found in Content-Disposition header.{COLOR_RESET}")
            return False


def fill_response(url):
    '''Returns head response for the given url'''
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
    '''Prompt user if they want to download file'''
    print(
        f"{COLOR_WARNING}Its seems its '{filetype}' file, you still want to download?{COLOR_RESET}")
    confirmation = {"yes", "ye", "y"}
    if not input(f"{COLOR_WARNING}Enter Y/y to download: ").lower() in confirmation:
        print(f"{COLOR_VERBOSE}Okay Bye!!{COLOR_RESET}")
        exit()
    else:
        print(COLOR_RESET, end="")


def calculate_chunk_sizes(connections, filelength):
    '''Returns chunksize for given connections and filelength'''
    remainder = filelength % connections
    filelength -= remainder
    chunksize = int(filelength / connections)
    return chunksize


def server_supports_range(response):
    '''Returns True if server accepts range requests'''
    if not response.headers.get("Accept-Ranges"):
        return False
    else:
        return True


def write_to_file(filename, data):
    '''Writes binary given data to given filename'''
    with open(filename, 'ab') as f:
        f.write(data)


def report_progress(downloadedsize):
    '''Prints progress bar'''
    global downloadedfile
    downloadedfile += downloadedsize
    # print(f"{Fore.GREEN}", end="")
    bar.next(downloadedsize)
    # print(RESET, end="")
    if filelength <= downloadedfile:
        bar.finish()


def download_multipart(url, startrange, finishrange, id, outputfile):
    '''Download file in the given startrange and finishrange from url and write it to outputfile'''
    filename = f"{outputfile}.part{id}"
    chunksizetemp = 1024 * 500
    size = finishrange - startrange
    downloadeddata = 0
    starttemp = 0
    fintemp = 0
    if size < chunksizetemp:
        content = requests.get(url).content
        downloadeddata += content.__len__()
        write_to_file(filename, content)
        report_progress(content.__len__())
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
        try:
            header = {"Range": f"bytes={starttemp}-{fintemp}"}
            content = requests.get(url, headers=header).content
            downloadeddata += content.__len__()
        except gaierror as gaierr:
            print(f"{id}: {gaierr}")
        except NewConnectionError as nce:
            print(f"{id}: {nce}")
            exit()

        write_to_file(filename, content)
        report_progress(content.__len__())
        if path.getsize(filename) >= size:
            break


def download_singlepart(url, filename):
    '''Download content from given url and save it to filename'''    
    downloadeddata = 0
    content = requests.get(url).content
    downloadeddata += content.__len__()
    write_to_file(filename, content)
    report_progress(content.__len__())
    exit()


def main():
    '''Main function'''
    global url
    url = fill_url()
    global response
    response = fill_response(url)
    global outputfilename
    outputfilename = fill_file()
    global connections
    connections = fill_connections()
    global filelength
    global bar
    if connections > 1:
        supportsmulticonnections = True
    else:
        supportsmulticonnections = False

    try:
        filelength = int(response.headers.get("Content-Length"))
        if filelength < 1025 * 500:
            supportsmulticonnections = False
    except TypeError as te:
        print(
            f"{COLOR_WARNING}Server did not tell the file size, so have to use single connection.{COLOR_RESET}")
        supportsmulticonnections = False

    if not server_supports_range(response):
        print(f"{COLOR_WARNING}Sorry, server does not accept ranges{COLOR_RESET}")
        chunksize = filelength
        supportsmulticonnections = False
    elif supportsmulticonnections:
        chunksize = calculate_chunk_sizes(connections, filelength)

    if verbose:
        print(f"\r{COLOR_DEBUG}Connections: {connections},\nURL: {url},\nOutput File: {outputfilename}," +
              f"\nFileLength: {filelength} Bytes\nSupports Multiple Connection Download: {supportsmulticonnections}\n{COLOR_RESET}")

    if not supportsmulticonnections:
        print(f"{COLOR_VERBOSE}Single connection mode!{COLOR_RESET}")
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

        print(f"{COLOR_VERBOSE}Starting...{COLOR_RESET}")
        try:
            for thread in threaddpool:
                thread.start()
            if verbose:
                print(
                    f"\r{COLOR_VERBOSE}Main: All threads started{COLOR_RESET}\n")

            for thread in threaddpool:
                thread.join()
            bar.finish()
            if verbose:
                print(f"\r{COLOR_VERBOSE}Main thread free!{COLOR_RESET}\n")
            with open(outputfilename, 'wb') as finalfile:
                for con in range(connections):
                    file = f"{outputfilename}.part{con}"
                    f = open(file, 'rb')
                    for line in f.readlines():
                        finalfile.write(line)
                    f.close()
                    os.remove(file)
            print(f"{COLOR_VERBOSE} Download complete!!{COLOR_RESET}")
        except Exception as ex:
            print(ex)
            exit()


if __name__ == "__main__":
    main()

# TODO: Implement feature to let user provide/download multiple urls
# TODO: Implement feature to let user stop program in the middle of downloading
# TODO: Implement mechanism to handle connection error in the middle of downloading
# TODO: Implement feature to let user choose destination directory for the downloaded file