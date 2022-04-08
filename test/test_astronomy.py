from unittest import TestCase
import datetime

from metoffice import astronomy


class TestAstronomy(TestCase):
    def setUp(self):
        # Setup contains mocks for xbmc modules that would normally
        # not be found in an isolated test environment.
        super(TestAstronomy, self).setUp()

    def test_basic(self):
        """
        Basic test to make sure that we get
        something moderately sensible back
        """
        sun = astronomy.Sun()
        # We get a sun object back
        self.assertTrue(isinstance(sun, astronomy.Sun))
        # which contains a sunrise datetime
        self.assertTrue(isinstance(sun.sunrise(), datetime.time))
        # and a sunset datetime
        self.assertTrue(isinstance(sun.sunset(), datetime.time))

    def test_known_time_place(self):
        """
        Given a known time and place we should get a known
        sunrise and sunset
        """
        from metoffice import astronomy
        london = (51.51, -0.13)
        today = datetime.datetime.strptime('Aug 5 2017', '%b %d %Y')
        sun = astronomy.Sun(*london)
        sunrise = sun.sunrise(today)
        sunset = sun.sunset(today)
        self.assertEqual(sunrise, datetime.time(4, 28, 38))
        self.assertEqual(sunset, datetime.time(19, 44, 39))
