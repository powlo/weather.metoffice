#A basic way of caching files associated with URLs
#with emphasis on caching results from urlretrieve.

"""
Add filter parameter to flush so that urls can be cleaned out according to pattern matching
Ie filter out any expired Rainfall Timestep 0.
"""

from datetime import datetime, timedelta
import time
import os
import shutil
import urllib
import json
import re

import xbmc

import utilities

class URLCache(object):
    TIME_FORMAT = "%a %b %d %H:%M:%S %Y"

    def __init__(self, file, folder):
        file_folder = os.path.dirname(file)
        if not file_folder:
            os.makedirs(file_folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

        self._file = file
        self._folder = folder

    def __enter__(self):
        try:
            file = open(self._file, 'r')
        except IOError:
            #create the file and try again.
            open(self._file, 'a').close()
            file = open(self._file, 'r')
        try:
            self._cache = json.load(file)
        except ValueError:
            self._cache = dict()
        file.close()
        return self

    def __exit__(self, type, value, traceback):
        with open(self._file, 'w+') as file:
            json.dump(self._cache, file, indent=2)

    def put(self, url, src, expiry):
        #takes a file and copies it into the cache
        #returns resource location in cache
        shutil.copy(src, self._folder)
        resource = os.path.join(self._folder, os.path.basename(src))
        self._cache[url] = {'resource':resource, 'expiry': expiry.strftime(self.TIME_FORMAT)}
        return resource

    def get(self, url):
        return self._cache[url]

    def remove(self, url):
        xbmc.log("Deleting file '%s'" % self._cache[url]['resource'])
        os.remove(self._cache[url]['resource'])
        xbmc.log("Removing entry for '%s' from cache" % url)
        del self._cache[url]

    def flush(self, pattern=None):
        flushlist = list()
        for url in self._cache:
            if pattern:
                if self.isexpired(self._cache[url]):
                    if re.match(pattern, url):
                        flushlist.append(url)
            else:
                if self.isexpired(entry):
                        flushlist.append(url)
        for url in flushlist:
            self.remove(url)

    def isexpired(self, entry):
        #the entry has expired, according to the 'expiry' field.
        expiry = datetime.fromtimestamp(time.mktime(time.strptime(entry['expiry'], self.TIME_FORMAT)))
        return expiry < datetime.now()

    def ismissing(self, entry):
        #the resource indicated by the entry no longer exists
        return not os.path.exists(entry['resource'])

    def setexpiry(self, url, expiry):
        """
        Sets the expiry of a given url
        """
        self._cache[url]['expiry'] = expiry.strftime(self.TIME_FORMAT)

    def urlretrieve(self, url, expiry=datetime.now()+timedelta(days=1)):
        """
        Checks to see if an item is in cache
        Uses urllib.urlretrieve to fetch the item
        NB. Assumes the url header type contains a valid file
        extension. This is true for application/json and image/png
        """
        try:
            xbmc.log("Checking cache for '%s'" % url)
            entry = self.get(url)
            if self.ismissing(entry):
                raise MissingError
            elif self.isexpired(entry):
                raise ExpiredError
            else:
                xbmc.log("Returning cached item.")
                return entry['resource']
        except (KeyError, MissingError):
            xbmc.log("Not in cache. Fetching from web.")
            (src, headers) = urllib.urlretrieve(url)
            if len(src.split('.')) == 1:
                ext = headers.type.split('/')[1]
                shutil.move(src, src+'.'+ext)
                src = src+'.'+ext
            return self.put(url, src, expiry)
        except ExpiredError:
            xbmc.log("Cached item has expired. Fetching from web.")
            resource = entry['resource']
            try:
                (src, headers) = urllib.urlretrieve(url)
                if len(src.split('.')) == 1:
                    ext = headers.type.split('/')[1]
                    shutil.move(src, src+'.'+ext)
                    src = src+'.'+ext
                resource = self.put(url, src, expiry)
            except URLError:
                xbmc.log("Fetch from web failed. Returning expired item.")
            finally:
                return resource

    def jsonretrieve(self, url, expiry=datetime.now()+timedelta(days=1)):
        with open(self.urlretrieve(url, expiry)) as file:
            try:
                return json.load(file)
            except ValueError:
                self.remove(url)
                xbmc.log('Couldn\'t load json data from %s' % file.name)
                raise

class MissingError(Exception):
    pass

class ExpiredError(Exception):
    pass