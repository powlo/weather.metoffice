import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock
from urllib import request

RESULTS_FOLDER = os.path.join(os.path.dirname(__file__), "results")


class TestURLCache(unittest.TestCase):
    def setUp(self):
        # create a disposable area for testing
        super(TestURLCache, self).setUp()
        try:
            os.mkdir(RESULTS_FOLDER)
        except OSError:
            pass

        from metoffice import urlcache

        self.urlcache = urlcache
        from metoffice import utilities

        self.utilities = utilities

    def test_init(self):
        fyle = os.path.join(RESULTS_FOLDER, "cache.json")
        folder = os.path.join(RESULTS_FOLDER, "cache")
        cache = self.urlcache.URLCache(RESULTS_FOLDER)
        self.assertEqual(cache._file, fyle, "Cache _file property not assigned")
        self.assertEqual(cache._folder, folder, "Cache _folder property not assigned")

    def test_enter(self):
        fyle = os.path.join(RESULTS_FOLDER, "cache.json")
        folder = os.path.join(RESULTS_FOLDER, "cache")
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            self.assertEqual(cache._file, fyle, "Cache _file property not assigned")
            self.assertEqual(
                cache._folder, folder, "Cache _folder property not assigned"
            )
            self.assertEqual(cache._cache, dict(), "Cache dictionary not created.")
        self.assertTrue(os.path.isfile(fyle), "Cache file not created.")
        self.assertTrue(os.path.isdir(folder), "Cache folder not created.")

    def test_exit(self):
        # Test flush happens on exit
        url1 = "http://www.xbmc.org/"
        url2 = "http://www.google.com/"
        src1 = os.path.join(RESULTS_FOLDER, "file1.txt")
        src2 = os.path.join(RESULTS_FOLDER, "file2.txt")
        open(src1, "w").close()
        open(src2, "w").close()
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            cache._cache[url1] = {
                "resource": src1,
                "expiry": yesterday.strftime(cache.TIME_FORMAT),
            }
            cache._cache[url2] = {
                "resource": src2,
                "expiry": tomorrow.strftime(cache.TIME_FORMAT),
            }

        # Test file is written and contains only one entry
        with open(os.path.join(RESULTS_FOLDER, "cache.json")) as fh:
            cache_contents = json.load(fh)
        self.assertEqual(1, len(cache_contents), "Unexpected item in bagging area")
        self.assertTrue(url2 in cache_contents)
        entry = cache_contents[url2]
        self.assertEqual(
            tomorrow.strftime(self.urlcache.URLCache.TIME_FORMAT), entry["expiry"]
        )
        self.assertEqual(os.path.basename(src2), os.path.basename(entry["resource"]))

    def test_remove(self):
        url = "http://www.xbmc.org/"
        request.urlopen = Mock(
            side_effect=lambda x: tempfile.NamedTemporaryFile(dir=RESULTS_FOLDER)
        )
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            filename = cache.get(url, lambda x: datetime.now() + timedelta(hours=1))
            self.assertTrue(
                os.path.isfile(filename), "File should exist before removal."
            )
            cache.remove(url)
            self.assertFalse(os.path.isfile(filename), "File is still in cache.")
            self.assertFalse(url in cache._cache, "Entry is still in cache.")

    def test_flush(self):
        url = "http://www.xbmc.org/"
        request.urlopen = Mock(
            side_effect=lambda x: tempfile.NamedTemporaryFile(dir=RESULTS_FOLDER)
        )
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            filename = cache.get(url, lambda x: datetime.now() - timedelta(days=1))
            self.assertTrue(os.path.isfile(filename), "File should exist before flush.")
            cache.flush()
            self.assertFalse(os.path.isfile(filename), "File is still in cache.")
            self.assertFalse(url in cache._cache, "Entry is still in cache.")

    def test_erase(self):
        open(os.path.join(RESULTS_FOLDER, "cache.json"), "a").close()
        os.mkdir(os.path.join(RESULTS_FOLDER, "cache"))
        self.urlcache.URLCache(RESULTS_FOLDER).erase()
        self.assertFalse(os.path.isfile(os.path.join(RESULTS_FOLDER, "cache.json")))
        self.assertFalse(os.path.isdir(os.path.join(RESULTS_FOLDER, "cache")))

    def test_get(self):
        url = "http://www.xbmc.org/"
        request.urlopen = Mock(
            side_effect=lambda x: tempfile.NamedTemporaryFile(dir=RESULTS_FOLDER)
        )
        mock_expiry_callback = Mock(return_value=datetime.now() + timedelta(days=1))
        mock_resource_callback = Mock()
        with self.urlcache.URLCache(RESULTS_FOLDER) as cache:
            # check item is fetched from the internet
            cache.get(url, mock_expiry_callback, mock_resource_callback)
            self.assertTrue(request.urlopen.called)
            self.assertTrue(mock_expiry_callback.called)
            self.assertTrue(mock_resource_callback.called)

            # check item is not fetched from internet
            request.urlopen.reset_mock()
            mock_expiry_callback.reset_mock()
            mock_resource_callback.reset_mock()
            filename = cache.get(url, mock_expiry_callback, mock_resource_callback)
            self.assertFalse(request.urlopen.called)
            self.assertFalse(mock_expiry_callback.called)
            self.assertFalse(mock_resource_callback.called)

            # check item is fetched because its invalid
            os.remove(filename)
            request.urlopen.reset_mock()
            mock_expiry_callback.reset_mock()
            mock_resource_callback.reset_mock()
            cache.get(url, mock_expiry_callback, mock_resource_callback)
            self.assertTrue(request.urlopen.called)
            self.assertTrue(mock_expiry_callback.called)
            self.assertTrue(mock_resource_callback.called)

            # check an exception is modified and reraised when exception occurs with urlopen
            request.urlopen.reset_mock()
            mock_expiry_callback.reset_mock()
            mock_resource_callback.reset_mock()
            request.urlopen = Mock(
                side_effect=request.URLError("Name or service not known")
            )
            cache.remove(url)
            with self.assertRaises(request.URLError) as cm:
                cache.get(url, mock_expiry_callback, mock_resource_callback)
            self.assertEqual(
                ("<urlopen error Name or service not known>", "http://www.xbmc.org/"),
                cm.exception.args,
            )

    def tearDown(self):
        shutil.rmtree(RESULTS_FOLDER)
        super(TestURLCache, self).tearDown()


if __name__ == "__main__":
    unittest.main()
