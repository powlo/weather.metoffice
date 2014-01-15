#A basic way of caching files associated with URLs
#with emphasis on caching results from urlretrieve.

from datetime import datetime, timedelta
import time
import os
import shutil
import urllib
import json

class URLCache(object):
    TIME_FORMAT = "%a %b %d %H:%M:%S %Y"

    def __init__(self, filename, folder):
        self._cachefilename = filename
        self._cachefolder = folder
        
    def __enter__(self):
        try:
            file = open(self._cachefilename, 'r')
        except IOError:
            #create the file and try again.
            open(self._cachefilename, 'a').close()
            file = open(self._cachefilename, 'r')            
        try:
            self._cachetable = json.load(file)
        except ValueError:
            self._cachetable = dict()
        file.close()
        return self

    def __exit__(self, type, value, traceback):
        with open(self._cachefilename, 'w+') as file:
            json.dump(self._cachetable, file, indent=2)
        
    def put(self, url, src, expiry):
        #takes a file and copies it into the cache
        shutil.copy(src, self._cachefolder)
        resource = os.path.join(self._cachefolder, os.path.basename(src))
        self._cachetable[url] = {'resource':resource, 'expiry': expiry.strftime(self.TIME_FORMAT)}

    def get(self, url):
        try:
            entry = self._cachetable[url]
            expired = self.isexpired(entry)
        except:
            expired = True
        if not expired:
            return entry['resource']
        else:
            return None 

    def remove(self, url):
        del self._cachetable[url]

    def flush(self):
        #flush should 1) delete expired, 2) remove null targets 3) remove null sources
        expired = list()
        for entry in self._cachetable:
            if self.isexpired(entry):
                expired.append(entry)
        for e in expired:
            del self._cachedata[e]

    def isexpired(self, entry):
        try:
            expiry = datetime.fromtimestamp(time.mktime(time.strptime(entry['expiry'], self.TIME_FORMAT)))
            if expiry > datetime.now():
                return False
        except:
            return True

    def urlretrieve(self, url, expiry, mode='r'):
        try:
            entry = self._cachetable[url]
            expired = self.isexpired(entry)
        except:
            expired = True
        if expired:
            src = urllib.urlretrieve(url)[0]
            self.put(url, src, expiry)
        resource = self.get(url)
        return open(resource, mode)