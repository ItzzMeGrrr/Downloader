try:
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
except ModuleNotFoundError as mnf:
    print(f"{mnf.msg}\nPlease run 'pip install -r requirements.txt' to install required modules")
    exit()

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
                    type=str, nargs=1, help="Save downloaded file as ")
parser.add_argument('-v', '--verbose', action="store_true",
                    help="Get verbose output")
argv = parser.parse_args()

connections = 1
outputfilename = "./temp"
url = ""
response = ""
filelength = 0
verbose = False

if(argv.__getattribute__("file")):
    fetch = False
else:
    fetch = True
if(argv.__getattribute__("verbose")):
    verbose = True
downloadedfile = 0
bar = ChargingBar("Downloading")
error_occured = False


def fill_url():
    '''Returns `url` from argv'''
    if argv.__getattribute__("url"):
        url = str(argv.__getattribute__("url")[0])
        url = urllib.parse.unquote(url)
        if argv.__getattribute__("url").__len__() > 1:
            print(
                f"{COLOR_WARNING}Current we support only one file download, so all urls except '{url}' will be ignored!{COLOR_RESET}")
        try:
            if verbose:
                print(
                    f"\r{COLOR_VERBOSE}Checking connection to url...{COLOR_RESET}")
            requests.head(url)
            if verbose:
                print(f"\r{COLOR_VERBOSE}Connection successful!{COLOR_RESET}")
        except requests.ConnectionError as ce:
            print(
                f"{COLOR_ERROR}Could not connect to {url}, please check the url or your internet connection.{COLOR_RESET}")
            exit()
        except requests.exceptions.MissingSchema as missingschema:
            print(f"{COLOR_ERROR}" +
                  str(missingschema)+f"{COLOR_RESET}")
            exit()
        except Exception as e:
            print(e)
            exit()
    else:
        print(f"{COLOR_ERROR}URL not found!{COLOR_RESET}")
        exit()
    return url


def fill_connections():
    '''Returns `connections` from argv'''
    if argv.__getattribute__("connections"):
        connections = int(argv.__getattribute__("connections")[0])
        return connections
    else:
        return 1


def fill_file():
    '''Returns `filename` from argv'''
    global response
    global url
    global fetch
    try:
        if argv.__getattribute__("file"):
            file = path.abspath(argv.__getattribute__("file")[0])
            # if the directory does not exist, create it
            if not path.exists(path.dirname(file)):
                raise FileNotFoundError()
            elif not path.basename(file):  # if filename is not valid
                file = get_filename_dynamically()
            else:
                if fetch:  # if filename not provided, try to get the name from url or something
                    file = get_filename_dynamically()

        else:
            if verbose:
                print(
                    f"\r{COLOR_WARNING}File name not provided, so going with filename from url if possible.{COLOR_RESET}")

            file = get_filename_dynamically()

    except FileNotFoundError as fnf:
        print(
            f"{COLOR_ERROR}Invalid path: {argv.__getattribute__('file')[0]}{COLOR_RESET}")
        exit(1)
    return file


def get_filename_dynamically():
    '''Returns filename from url'''
    global response
    global url
    file = retrieve_filename(response, url)
    if type(file) == str:  # try to determine the file extention
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
    return file


def retrieve_filename(response, url):
    '''Tries to retrieve `filename` from `url` or Content-Disposition header otherwise generates a random name'''
    tempurl = urllib.parse.urlparse(url)
    tempfilename = path.basename(tempurl.path)
    if tempfilename:
        return str(tempfilename)
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

                return generate_random_name()
            else:
                if verbose:
                    print(
                        f"\r{COLOR_WARNING}Filename not found in Content-Disposition header.{COLOR_RESET}\n")
                return generate_random_name()
        except IndexError as ie:
            print(
                f"{COLOR_WARNING}Filename not found in Content-Disposition header.{COLOR_RESET}")
            return generate_random_name()


def generate_random_name():
    '''Returns a random name of length 10'''
    randomname = ''.join(random.choices(
        string.ascii_letters + string.digits, k=10))
    return randomname


def fill_response(url):
    '''Returns head response for the given `url`'''
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
        print(f"{COLOR_VERBOSE}Okay Bye!{COLOR_RESET}")
        exit()
    else:
        print(COLOR_RESET, end="")


def calculate_chunk_sizes(connections, filelength):
    '''Returns `chunksize` for given connections and `filelength`'''
    remainder = filelength % connections
    filelength -= remainder
    chunksize = int(filelength / connections)
    return chunksize


def server_supports_range(response):
    '''Returns True if server supports range'''
    if not response.headers.get("Accept-Ranges"):
        return False
    else:
        return True


def write_to_file(filename, data):
    '''Writes given binary `data` to given `filename`'''
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
    '''Download file in the given `startrange` and `finishrange` from `url` and write it to `outputfile`'''
    if(argv.__getattribute__("file")):
        filename = argv.__getattribute__("file")
    filename = f"{outputfile}.part{id}"
    chunksizetemp = 1024 * 500
    size = finishrange - startrange
    downloadeddata = 0
    starttemp = 0
    fintemp = 0
    global stop
    global error_occured
    if size < chunksizetemp:
        content = requests.get(url, timeout=5).content
        downloadeddata += content.__len__()
        write_to_file(filename, content)
        report_progress(content.__len__())
        exit()
    while downloadeddata < size or not stop:
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
            content = requests.get(url, headers=header, timeout=5).content
            downloadeddata += content.__len__()
        except requests.exceptions.ConnectionError as nce:
            if nce.__str__().__contains__("Failed to establish a new connection"):
                print(
                    f"{COLOR_ERROR}Thread {id}: Failed to establish a new connection!{COLOR_RESET}")
            elif nce.__str__().__contains__("Read timed out"):
                print(
                    f"{COLOR_ERROR}Thread {id}: Connection timed out! Please check your internet connection!{COLOR_RESET}")
            else:
                print(
                    f"{COLOR_ERROR}Thread {id}: Connection Error... {nce}{COLOR_RESET}")
            error_occured = True
            stop = True
            exit()
        except Exception as exc:
            print(f"Thread {id}: {exc}")
            error_occured = True
            stop = True
            exit()

        write_to_file(filename, content)
        if stop:
            break
        report_progress(content.__len__())
        if path.getsize(filename) >= size:
            break


def download(chunksize):
    threaddpool = []
    global bar
    global stop
    global verbose
    global connections
    bar = ChargingBar("Downloading ", max=filelength)
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

        alive_threads_count = connections
        dead_threads = []
        try:
            while alive_threads_count > 0:
                if stop:
                    break
                for thread in threaddpool:
                    if not thread.is_alive() and thread.getName() not in dead_threads:
                        alive_threads_count -= 1
                        dead_threads.append(thread.getName())
        except KeyboardInterrupt:
            stop = True
        if stop and not error_occured:
            print(f"\n{COLOR_VERBOSE}Waiting for threads to stop...{COLOR_RESET}")
        for thread in threaddpool:
            thread.join()
        bar.finish()
        if not stop:
            with open(outputfilename, 'wb') as finalfile:
                for con in range(connections):
                    file = f"{outputfilename}.part{con}"
                    if path.exists(file):
                        f = open(file, 'rb')
                        for line in f.readlines():
                            finalfile.write(line)
                        f.close()
                        os.remove(file)
        else:
            if verbose:
                print(f"{COLOR_VERBOSE}Cleaning residual files...{COLOR_RESET}")
            for con in range(connections):
                file = f"{outputfilename}.part{con}"
                if path.exists(file):
                    os.remove(file)

    except Exception as ex:
        print(ex)
        exit()


def download_singlepart(url, filename):
    '''Download content from given `url` and save it to `filename`'''
    downloadeddata = 0
    global filelength
    global bar
    global stop
    global error_occured
    content_stream = requests.get(url, stream=True, timeout=5)
    if path.exists(filename):
        if not input(f"{COLOR_WARNING}File '{filename}' already exists! Do you want to overwrite it?(Y/y): ").lower() in {"yes", "ye", "y"}:
            print(f"{COLOR_VERBOSE}Ok Bye!{COLOR_RESET}")
            exit()
        else:
            os.remove(filename)
            print(f"{COLOR_RESET}")

    partfile = f"{filename}.part"
    if not path.exists(partfile):
        with open(partfile, "x"):  # create file if not exists
            pass
    else:
        with open(partfile, "w"):  # delete file content if file already exists
            pass
    if filelength:
        bar = ChargingBar("Downloading ", max=filelength)

    try:
        with open(partfile, "wb") as file:
            for chunk in content_stream.iter_content(1024*500):
                file.write(chunk)
                downloadeddata += chunk.__len__()
                if not filelength:
                    print(
                        f"\r{COLOR_VERBOSE}Downloaded: {downloadeddata/(1024*1024)} MB      {COLOR_RESET}", end="")
                else:
                    if downloadeddata <= filelength:
                        report_progress(chunk.__len__())
                    else:
                        bar.finish()
                        break

    except KeyboardInterrupt:
        print(
            f"\n{COLOR_ERROR}Download Cancelled! Downloaded {downloadeddata/(1024*1024)} MB{COLOR_RESET}")
        os.remove(partfile)
        exit()
    except requests.exceptions.ConnectionError as nce:
        if nce.__str__().__contains__("Failed to establish a new connection"):
            print(
                f"\n{COLOR_ERROR} Failed to establish a new connection!{COLOR_RESET}")
        elif nce.__str__().__contains__("Read timed out"):
            print(
                f"\n{COLOR_ERROR}Connection timed out! Please check your internet connection!{COLOR_RESET}")
        else:
            print(
                f"\n{COLOR_ERROR}Connection Error... {nce}{COLOR_RESET}")
        error_occured = True
        stop = True
    if not stop:
        try:
            if path.exists(filename):
                os.remove(filename)
            os.rename(partfile, filename)
        except PermissionError:
            with open(filename, "wb") as finalfile:
                with open(partfile, "rb") as file:
                    for line in file.readlines():
                        finalfile.write(line)
            os.remove(partfile)
    else:
        if path.exists(partfile):
            os.remove(partfile)


def main():
    '''Main function'''
    global url
    global filelength
    global bar
    global stop
    global response
    global outputfilename
    global connections
    global fetch

    url = fill_url()
    response = fill_response(url)
    outputfilename = fill_file()
    connections = fill_connections()
    stop = False

    if connections > 1:
        supportsmulticonnections = True
    else:
        supportsmulticonnections = False

    try:
        filelength = int(response.headers.get("Content-Length"))
        if filelength < 1025 * 500:
            supportsmulticonnections = False
    except TypeError:
        print(
            f"{COLOR_WARNING}Server did not tell the file size, so have to use single connection.{COLOR_RESET}")
        filelength = False
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
        print(f"{COLOR_VERBOSE}Multiple connection mode!{COLOR_RESET}")
        download(chunksize)
    if not stop:
        print(f"{COLOR_VERBOSE} Download complete!{COLOR_RESET}")
    elif error_occured:
        print(f"{COLOR_ERROR} Download could not be completed!{COLOR_RESET}")
    else:
        print(f"{COLOR_ERROR} Download Cancelled!{COLOR_RESET}")

    if verbose:
        print(f"\r{COLOR_VERBOSE}Main thread free!{COLOR_RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"{COLOR_ERROR}Cancelled by user!{COLOR_RESET}")
        stop = True
        exit()

# TODO: Implement feature to let user provide/download multiple urls
# TODO: Implement feature to let user choose destination directory for the downloaded file
