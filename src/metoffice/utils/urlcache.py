#A basic way of caching files associated with URLs
#with emphasis on caching results from urlretrieve.

"""
Add filter parameter to flush so that urls can be cleaned out according to pattern matching
Ie filter out any expired Rainfall Timestep 0.
"""

from datetime import datetime, timedelta
import os
import shutil
import urllib
import json
import re

import utilities


class Entry(object):
    TIME_FORMAT = "%a %b %d %H:%M:%S %Y"

    def __init__(self, resource, expiry):
        self.resource = resource
        self.expiry = expiry

    def isvalid(self):
        #check the entry expiry and the resource exists.
        return self.expiry > datetime.now() and os.path.exists(self.resource)

class EntryEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Entry):
            return {'resource' : obj.resource,
                 'expiry' : obj.expiry.strftime(Entry.TIME_FORMAT)}
        else:
            return json.JSONEncoder.default(self, obj)

def entry_decoder(obj):
    if 'expiry' in obj and 'resource' in obj:
        return Entry(obj['resource'], utilities.strptime(obj['expiry'], Entry.TIME_FORMAT))
    return obj

class URLCache(object):

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
            self._cache = json.load(fyle, object_hook=entry_decoder)
        except ValueError:
            self._cache = dict()
        fyle.close()
        return self

    def __exit__(self, typ, value, traceback):
        self.flush()
        with open(self._file, 'w+') as fyle:
            json.dump(self._cache, fyle, indent=2,cls=EntryEncoder)

    #Todo: Make put take an Entry object
    def put(self, url, src, expiry):
        #takes a file and copies it into the cache
        #returns resource location in cache
        shutil.move(src, self._folder)
        resource = os.path.join(self._folder, os.path.basename(src))
        self._cache[url] = Entry(resource, expiry)

    def get(self, url):
        return self._cache[url]

    def remove(self, url):
        if url in self._cache:
            entry = self._cache[url]
            utilities.log("Deleting file '%s'" % entry.resource)
            os.remove(entry.resource)
            utilities.log("Removing entry for '%s' from cache" % url)
            del self._cache[url]

    def flush(self):
        flushlist = list()
        for url, entry in self._cache.iteritems():
            if not entry.isvalid():
                    flushlist.append(url)
        for url in flushlist:
            self.remove(url)

    def urlretrieve(self, url, expiry=datetime.now()+timedelta(days=1)):
        """
        Checks to see if an item is in cache
        Uses urllib.urlretrieve to fetch the item
        NB. Assumes the url header type contains a valid file
        extension. This is true for application/json and image/png
        """
        try:
            entry = self.get(url)
            if not entry.isvalid():
                raise InvalidCacheError
            else:
                utilities.log("Returning cached item for '%s'" % url)
                return entry
        except (KeyError, InvalidCacheError):
            utilities.log("Fetching '%s' from web." % url)
            (src, headers) = urllib.urlretrieve(url)
            self.put(url, src, expiry)
            return self.get(url)

    def jsonretrieve(self, url, expiry=datetime.now()+timedelta(days=1)):
        entry = self.urlretrieve(url, expiry)
        with open(entry.resource) as fyle:
            try:
                return json.load(fyle)
            except ValueError:
                self.remove(url)
                utilities.log('Couldn\'t load json data from %s' % fyle.name)
                raise

class InvalidCacheError(Exception):
    pass