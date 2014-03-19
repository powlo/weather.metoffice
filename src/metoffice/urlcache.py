#A basic way of caching files associated with URLs
#with emphasis on caching results from urlretrieve.

"""
Add filter parameter to flush so that urls can be cleaned out according to pattern matching
Ie filter out any expired Rainfall Timestep 0.
"""

from datetime import datetime
import os
import urllib2
import tempfile
import json

import utilities

class URLCache(object):
    TIME_FORMAT = "%a %b %d %H:%M:%S %Y"

    def __init__(self, folder):
        self._folder = os.path.join(folder, 'cache')
        self._file = os.path.join(folder, 'cache.json')

    def __enter__(self):
        if not os.path.exists(self._folder):
            os.makedirs(self._folder)
        try:
            fyle = open(self._file, 'r')
        except IOError:
            #create the file and try again.
            open(self._file, 'a').close()
            fyle = open(self._file, 'r')
        try:
            self._cache = json.load(fyle)
        except ValueError:
            self._cache = dict()
        fyle.close()
        return self

    def __exit__(self, typ, value, traceback):
        self.flush()
        with open(self._file, 'w+') as fyle:
            json.dump(self._cache, fyle, indent=2)

    def remove(self, url):
        if url in self._cache:
            entry = self._cache[url]
            utilities.log("Deleting file '%s'" % entry['resource'])
            os.remove(entry['resource'])
            utilities.log("Removing entry for '%s' from cache" % url)
            del self._cache[url]

    def flush(self):
        flushlist = list()
        for url, entry in self._cache.iteritems():
            if not os.path.isfile(entry['resource']) or utilities.strptime(entry['expiry'], self.TIME_FORMAT) < datetime.now():
                    flushlist.append(url)
        for url in flushlist:
            self.remove(url)

    def get(self, url, expiry_callback):
        """
        Checks to see if an item is in cache
        """
        try:
            entry = self._cache[url]
            if not os.path.isfile(entry['resource']) or utilities.strptime(entry['expiry'], self.TIME_FORMAT) < datetime.now():
                raise InvalidCacheError
            else:
                utilities.log("Returning cached item for '%s'" % url)
                return open(entry['resource'])
        except (KeyError, InvalidCacheError):
            utilities.log("Fetching '%s' from web." % url)
            #(src, headers) = urllib.urlretrieve(url)
            response = urllib2.urlopen(url)
            page = response.read()
            response.close()
            tmp = tempfile.NamedTemporaryFile(dir=self._folder, delete=False)
            tmp.write(page)
            tmp.close()
            expiry = expiry_callback(open(tmp.name))
            self._cache[url] = {'resource': tmp.name, 'expiry': expiry.strftime(self.TIME_FORMAT)}
            return open(tmp.name)

class InvalidCacheError(Exception):
    pass