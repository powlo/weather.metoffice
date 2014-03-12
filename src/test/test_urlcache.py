import os
import shutil
import unittest
from datetime import datetime, timedelta
import urllib
import json
from mock import Mock

from xbmctestcase import XBMCTestCase

RESULTS_FOLDER = 'results'

class TestEntry(XBMCTestCase):
    def setUp(self):
        #create a disposable area for testing
        super(TestEntry, self).setUp()
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

        from metoffice.utils import urlcache
        self.urlcache = urlcache

    def test_init(self):
        src = os.path.join(RESULTS_FOLDER, 'file.txt')
        now = datetime.now()
        e = self.urlcache.Entry(src, now)
        self.assertEqual(src, e.resource)
        self.assertEqual(now, e.expiry)

    def test_isvalid(self):
        #test what happens when the resource is expired
        src = os.path.join(RESULTS_FOLDER, 'file.txt')
        open(src, 'w').close()
        yesterday = datetime.now() - timedelta(days=1)
        e = self.urlcache.Entry(src, yesterday)
        self.assertFalse(e.isvalid())
        tomorrow = datetime.now() + timedelta(days=1)
        e.expiry = tomorrow
        self.assertTrue(e.isvalid())

        #test what happens when the resource is missing
        os.remove(src)
        self.assertFalse(e.isvalid())
        open(src, 'w').close()
        self.assertTrue(e.isvalid())

    def tearDown(self):
        shutil.rmtree(RESULTS_FOLDER)
        super(TestEntry, self).tearDown()

class TestURLCache(XBMCTestCase):
    def setUp(self):
        #create a disposable area for testing
        super(TestURLCache, self).setUp()
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass
        
        from metoffice.utils import urlcache
        self.urlcache = urlcache
        from metoffice.utils import utilities
        self.utilities = utilities

    def test_init(self):
        fyle = os.path.join(RESULTS_FOLDER, 'cache.json')
        folder = os.path.join(RESULTS_FOLDER, 'cache')
        cache = self.urlcache.URLCache(RESULTS_FOLDER)
        self.assertEqual(cache._file, fyle, 'Cache _file property not assigned')
        self.assertEqual(cache._folder, folder, 'Cache _folder property not assigned')

    def test_enter(self):
        fyle = os.path.join(RESULTS_FOLDER, 'cache.json')
        folder = os.path.join(RESULTS_FOLDER, 'cache')
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            self.assertEqual(cache._file, fyle, 'Cache _file property not assigned')
            self.assertEqual(cache._folder, folder, 'Cache _folder property not assigned')
            self.assertEqual(cache._cache, dict(), 'Cache dictionary not created.')
        self.assertTrue(os.path.isfile(fyle), 'Cache file not created.')
        self.assertTrue(os.path.isdir(folder), 'Cache folder not created.')

    def test_put(self):
        url = 'http://www.xbmc.org/'
        src = open(os.path.join(RESULTS_FOLDER, 'putfile.txt'), 'w').name
        expiry = datetime.now() + timedelta(days=1)
        dest = os.path.join(RESULTS_FOLDER, 'cache', os.path.basename(src))
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            cache.put(url, src, expiry)
            self.assertTrue(os.path.isfile(dest), 'File not copied into cache.')
            self.assertTrue(url in cache._cache, 'Entry not created in cache.')
            
    def test_get(self):    
        url = 'http://www.xbmc.org/'
        src = open(os.path.join(RESULTS_FOLDER, 'putfile.txt'), 'w').name
        dest = os.path.join(RESULTS_FOLDER, 'cache', os.path.basename(src))
        expiry = datetime.now() + timedelta(days=2)
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            cache.put(url, src, expiry)
            entry = cache.get(url)
            self.assertEqual(dest, entry.resource, 'Cache resource mismatch.')
            self.assertEqual(expiry, entry.expiry, 'Cache expiry mismatch.')
    
    def test_remove(self):
        url = 'http://www.xbmc.org/'
        src = open(os.path.join(RESULTS_FOLDER, 'putfile.txt'), 'w').name
        expiry = datetime.now() + timedelta(days=1)
        dest = os.path.join(RESULTS_FOLDER, 'cache', os.path.basename(src))
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            cache.put(url, src, expiry)
            cache.remove(url)
            self.assertFalse(os.path.isfile(dest), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')
    
    def test_flush(self):
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(RESULTS_FOLDER, 'putfile.txt'), 'w').name
            expiry = datetime.now() - timedelta(days=1)
            dest = os.path.join(cache._folder, os.path.basename(src))
            cache.put(url, src, expiry)
            cache.flush()
            self.assertFalse(os.path.isfile(dest), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')

            src = open(os.path.join(RESULTS_FOLDER, 'putfile.txt'), 'w').name
            cache.put(url, src, expiry)
            cache.flush('.*xbmc.*')
            self.assertFalse(os.path.isfile(dest), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')

            src = open(os.path.join(RESULTS_FOLDER, 'putfile.txt'), 'w').name
            cache.put(url, src, expiry)
            cache.flush('.*google.*')
            self.assertTrue(os.path.isfile(dest), 'File removed from cache.')
            self.assertTrue(url in cache._cache, 'Entry removed from cache.')

    def test_urlretrieve(self):
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(RESULTS_FOLDER, 'tmp_af54mPh'), 'w').name
            dest = os.path.join(RESULTS_FOLDER, 'cache', os.path.basename(src)+".json")
            header = Mock()
            header.type = 'application/json'
            urllib.urlretrieve = Mock(return_value=(src, header))

            #check item is fetched from the internet
            cache.urlretrieve(url)
            self.assertTrue(urllib.urlretrieve.called) #@UndefinedVariable

            #check item is not fetched from internet
            urllib.urlretrieve.reset_mock() #@UndefinedVariable
            cache.urlretrieve(url)
            self.assertFalse(urllib.urlretrieve.called) #@UndefinedVariable

            #check item is fetched because its invalid
            src = open(os.path.join(RESULTS_FOLDER, 'tmp_af54mPh'), 'w').name
            urllib.urlretrieve.reset_mock() #@UndefinedVariable
            entry = cache.get(url)
            entry.expiry = datetime.now() - timedelta(days=1)
            os.remove(entry.resource)
            cache.urlretrieve(url)
            self.assertTrue(urllib.urlretrieve.called) #@UndefinedVariable

            #check exception code
            entry = cache.get(url)
            entry.expiry = datetime.now() - timedelta(days=1)
            urllib.urlretrieve = Mock(side_effect=IOError)
            with self.assertRaises(IOError):
                cache.urlretrieve(url)

    def test_jsonretrieve(self):
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            filename = os.path.join(RESULTS_FOLDER, 'tmp_af54mPh')
            dest = os.path.join(RESULTS_FOLDER, 'cache', 'tmp_af54mPh')
            src = open(filename, 'w')
            src.write("{}")
            src.close()
            cache.put(url, filename, datetime.now()+timedelta(hours=1))
            entry = cache.get(url)
            cache.urlretrieve = Mock(return_value=entry)
            self.assertEqual(dict(), cache.jsonretrieve(url))

            #test exception
            #filename = os.path.join(RESULTS_FOLDER, 'cache', 'tmp_af54mPh')
            src = open(entry.resource, 'w').close()
            with self.assertRaises(ValueError):
                cache.jsonretrieve(url)
            with self.assertRaises(KeyError):
                cache.get(url)

    def test_entry_decoder(self):
        #test basic decoding
        json_str= '{"cat":"dog"}'
        obj = json.loads(json_str, object_hook=self.urlcache.entry_decoder)
        self.assertEqual({'cat':'dog'}, obj)
        
        #test Entry decoding
        json_str = '{"resource": "/path/to/something", "expiry": "Wed Mar 12 18:31:44 2014"}'
        obj = json.loads(json_str, object_hook=self.urlcache.entry_decoder)
        self.assertIsInstance(obj, self.urlcache.Entry)
        self.assertEqual('/path/to/something', obj.resource)
        self.assertEqual(self.utilities.strptime("Wed Mar 12 18:31:44 2014", self.urlcache.Entry.TIME_FORMAT), obj.expiry)

    def tearDown(self):
        shutil.rmtree(RESULTS_FOLDER)
        super(TestURLCache, self).tearDown()


        
if __name__ == '__main__':
    unittest.main()