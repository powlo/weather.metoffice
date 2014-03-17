import os
import shutil
import unittest
from datetime import datetime, timedelta
import urllib2
import json
import tempfile
from mock import Mock

from xbmctestcase import XBMCTestCase

RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), 'results')

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

    def test_exit(self):
        #Test flush happens on exit
        url1 = 'http://www.xbmc.org/'
        url2 = 'http://www.google.com/'
        src1 = os.path.join(RESULTS_FOLDER, 'file1.txt')
        src2 = os.path.join(RESULTS_FOLDER, 'file2.txt')
        open(src1, 'w').close()
        open(src2, 'w').close()
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            cache._cache[url1] = self.urlcache.Entry(src1, yesterday)
            cache._cache[url2] = self.urlcache.Entry(src2, tomorrow)

        #Test file is written and contains only one entry
        f = open(os.path.join(RESULTS_FOLDER, 'cache.json'))
        cache_contents = json.load(f, object_hook=self.urlcache.entry_decoder)
        self.assertEqual(1, len(cache_contents), "Unexpected item in bagging area")
        self.assertTrue(cache_contents.has_key(url2))
        entry = cache_contents[url2]
        self.assertEqual(datetime.strptime(datetime.strftime(tomorrow, self.urlcache.Entry.TIME_FORMAT), self.urlcache.Entry.TIME_FORMAT), entry.expiry)
        self.assertEqual(os.path.basename(src2), os.path.basename(entry.resource))

    def test_remove(self):
        url = 'http://www.xbmc.org/'
        urllib2.urlopen = Mock(side_effect=lambda x: tempfile.NamedTemporaryFile(dir=RESULTS_FOLDER))
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            with cache.get(url, lambda x: datetime.now()+timedelta(hours=1)) as f:
                filename = f.name
            self.assertTrue(os.path.isfile(filename), 'File should exist before removal.')
            cache.remove(url)
            self.assertFalse(os.path.isfile(filename), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')
    
    def test_flush(self):
        url = 'http://www.xbmc.org/'
        urllib2.urlopen = Mock(side_effect=lambda x: tempfile.NamedTemporaryFile(dir=RESULTS_FOLDER))
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            with cache.get(url, lambda x: datetime.now() - timedelta(days=1)) as f:
                filename = f.name
            self.assertTrue(os.path.isfile(filename), 'File should exist before flush.')
            cache.flush()
            self.assertFalse(os.path.isfile(filename), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')

    def test_get(self):
        url = 'http://www.xbmc.org/'
        urllib2.urlopen = Mock(side_effect=lambda x: tempfile.NamedTemporaryFile(dir=RESULTS_FOLDER))
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            #check item is fetched from the internet
            cache.get(url, lambda x: datetime.now()+timedelta(hours=1)).close()
            self.assertTrue(urllib2.urlopen.called) #@UndefinedVariable

            #check item is not fetched from internet
            urllib2.urlopen.reset_mock() #@UndefinedVariable
            f = cache.get(url, lambda x: datetime.now()+timedelta(hours=1))
            f.close()
            self.assertFalse(urllib2.urlopen.called) #@UndefinedVariable

            #check item is fetched because its invalid
            os.remove(f.name)
            urllib2.urlopen.reset_mock() #@UndefinedVariable
            cache.get(url, lambda x: datetime.now()+timedelta(hours=1))
            self.assertTrue(urllib2.urlopen.called) #@UndefinedVariable

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