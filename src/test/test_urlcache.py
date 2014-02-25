import os
import shutil
import unittest
from datetime import datetime, timedelta
import urllib
from mock import patch, Mock

TEST_FOLDER = 'testlab'
CACHE_FOLDER = os.path.join(TEST_FOLDER, 'cache')
CACHE_FILE = os.path.join(TEST_FOLDER, 'cache.json')

class TestURLCache(unittest.TestCase):    
    def setUp(self):
        #Mock up any calls to modules that cannot be imported
        self.xbmc = Mock()
        self.xbmcgui = Mock()
        self.xbmcaddon = Mock()

        modules = {
            'xbmc' : self.xbmc,
            'xbmcgui': self.xbmcgui,
            'xbmcaddon': self.xbmcaddon
            }
        self.module_patcher = patch.dict('sys.modules', modules) #@UndefinedVariable
        self.addon_patcher = patch('xbmcaddon.Addon')
        self.translate_patcher = patch('xbmc.translatePath')
        self.log_patcher = patch('xbmc.log')
        self.module_patcher.start()
        self.addon_patcher.start()
        self.translate_patcher.start()

        #create a disposable area for testing
        try:
            os.mkdir(TEST_FOLDER)
        except OSError:
            pass
        
        from metoffice.utils.urlcache import URLCache 
        self.URLCache = URLCache
    
    def test_init(self):
        folder1 = os.path.join(TEST_FOLDER, 'folder1')
        folder2 = os.path.join(TEST_FOLDER, 'folder2')
        fyle = os.path.join(folder1, 'cache.json')
        self.assertFalse(os.path.exists(folder1), 'Folder already exists.')
        self.assertFalse(os.path.exists(folder2), 'Folder already exists.')
        cache = self.URLCache(fyle, folder2)
        self.assertTrue(os.path.isdir(folder1), 'Cache folder not created.')
        self.assertTrue(os.path.isdir(folder2), 'Cache folder not created.')
        self.assertEqual(cache._file, fyle, 'Cache _file property not assigned')
        self.assertEqual(cache._folder, folder2, 'Cache _folder property not assigned')

    def test_enter(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            self.assertTrue(os.path.isfile(CACHE_FILE), 'Cache file not created.')
            self.assertEqual(cache._cache, dict(), 'Cache dictionary not created.')

    def test_put(self):
        url = 'http://www.xbmc.org/'
        src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
        expiry = datetime.now() + timedelta(days=1)
        dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            cache.put(url, src, expiry)
            self.assertTrue(os.path.isfile(dest), 'File not copied into cache.')
            self.assertTrue(url in cache._cache, 'Entry not created in cache.')
            
    def test_get(self):    
        url = 'http://www.xbmc.org/'
        src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
        dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
        expiry = datetime.now() + timedelta(days=1)
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            cache.put(url, src, expiry)
            entry = cache.get(url)
            self.assertEqual(dest, entry['resource'], 'Cache resource mismatch.')
            self.assertEqual(expiry.strftime(cache.TIME_FORMAT), entry['expiry'], 'Cache expiry mismatch.')
    
    def test_remove(self):
        url = 'http://www.xbmc.org/'
        src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
        expiry = datetime.now() + timedelta(days=1)
        dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            cache.put(url, src, expiry)
            cache.remove(url)
            self.assertFalse(os.path.isfile(dest), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')
    
    def test_flush(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
            expiry = datetime.now() - timedelta(days=1)
            dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
            cache.put(url, src, expiry)
            cache.flush()
            self.assertFalse(os.path.isfile(dest), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')

            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
            expiry = datetime.now() - timedelta(days=1)
            dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
            cache.put(url, src, expiry)
            cache.flush('.*xbmc.*')
            self.assertFalse(os.path.isfile(dest), 'File is still in cache.')
            self.assertFalse(url in cache._cache, 'Entry is still in cache.')

            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
            expiry = datetime.now() - timedelta(days=1)
            dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
            cache.put(url, src, expiry)
            cache.flush('.*google.*')
            self.assertTrue(os.path.isfile(dest), 'File removed from cache.')
            self.assertTrue(url in cache._cache, 'Entry removed from cache.')
    
    def test_isexpired(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
            expiry = datetime.now() + timedelta(days=1)
            cache.put(url, src, expiry)
            entry = cache.get(url)
            self.assertFalse(cache.isexpired(entry), 'Entry identified as being expired')
            expiry = datetime.now() - timedelta(days=1)
            cache.put(url, src, expiry)
            entry = cache.get(url)
            self.assertTrue(cache.isexpired(entry), 'Entry not identified as being expired')

    def test_ismissing(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
            dest = os.path.join(CACHE_FOLDER, os.path.basename(src))
            expiry = datetime.now() - timedelta(days=1)
            cache.put(url, src, expiry)
            entry = cache.get(url)
            self.assertFalse(cache.ismissing(entry), 'Entry identified as being missing')
            os.remove(dest)
            self.assertTrue(cache.ismissing(entry), 'Entry identified as not missing')

    def test_setexpiry(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'putfile.txt'), 'w').name
            expiry = datetime.now() - timedelta(days=1)
            cache.put(url, src, expiry)
            expiry = datetime.now()
            entry = cache.get(url)
            self.assertNotEqual(expiry.strftime(cache.TIME_FORMAT), entry['expiry'], "Expiry shouldn't equal new expiry.")
            cache.setexpiry(url, expiry)
            entry = cache.get(url)
            self.assertEqual(expiry.strftime(cache.TIME_FORMAT), entry['expiry'], "Expiry was not updated.")
    
    def test_urlretrieve(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            src = open(os.path.join(TEST_FOLDER, 'tmp_af54mPh'), 'w').name
            dest = os.path.join(CACHE_FOLDER, os.path.basename(src)+".json")
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

            #check item is fetched because its expired
            src = open(os.path.join(TEST_FOLDER, 'tmp_af54mPh'), 'w').name
            urllib.urlretrieve.reset_mock() #@UndefinedVariable
            cache.setexpiry(url, datetime.now() - timedelta(days=1))
            cache.urlretrieve(url)
            self.assertTrue(urllib.urlretrieve.called) #@UndefinedVariable

            #check item is fetched because its missing
            src = open(os.path.join(TEST_FOLDER, 'tmp_af54mPh'), 'w').name
            os.remove(dest)
            urllib.urlretrieve.reset_mock() #@UndefinedVariable
            cache.urlretrieve(url)
            self.assertTrue(urllib.urlretrieve.called) #@UndefinedVariable

            #check exception code
            cache.setexpiry(url, datetime.now() - timedelta(days=1))
            urllib.urlretrieve = Mock(side_effect=IOError)
            with self.assertRaises(IOError):
                cache.urlretrieve(url)

    def test_jsonretrieve(self):
        with self.URLCache(CACHE_FILE, CACHE_FOLDER) as cache:
            url = 'http://www.xbmc.org/'
            filename =os.path.join(TEST_FOLDER, 'tmp_af54mPh')
            src = open(filename, 'w')
            src.write("{}")
            src.close()
            cache.urlretrieve = Mock(return_value=src.name)
            self.assertEqual(dict(), cache.jsonretrieve(url))

            #test exception
            src = open(filename, 'w').close()
            cache.put(url, filename, datetime.now()+timedelta(hours=1))
            with self.assertRaises(ValueError):
                cache.jsonretrieve(url)
            with self.assertRaises(KeyError):
                cache.get(url)

    def tearDown(self):
        shutil.rmtree('testlab')
        self.module_patcher.stop()
        self.addon_patcher.stop()
        self.translate_patcher.stop()

if __name__ == '__main__':
    unittest.main()