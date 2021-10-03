import sys
from contextlib import closing as C

import pycurl

class Writer:
   def __init__(self, file):
       self.file = file

   def write(self, data):
       sys.stderr.write(data)
       self.file.write(data)

   def close(self):
       self.file.close()

url = 'http://stackoverflow.com/questions/8909710/'
with C(pycurl.Curl()) as c, C(Writer(open('output','wb'))) as w:
    c.setopt(c.URL, url)
    c.setopt(c.WRITEFUNCTION, w.write)
    c.setopt(c.FOLLOWLOCATION, True)
    c.perform()
    print >>sys.stderr, c.getinfo(c.HTTP_CODE), c.getinfo(c.EFFECTIVE_URL)