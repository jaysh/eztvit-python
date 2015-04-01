import mock
import unittest
import eztvit

class TestEztvIt(unittest.TestCase):
    def _get_request_from_mock(self, mock_urlopen, call_number=1):
        (request, ) = mock_urlopen.call_args_list[call_number][0]

        return request

    @mock.patch('urllib2.urlopen')
    def test_suits_via_show_name(self, mock_urlopen):
        with open('tests/fixtures/homepage.html') as fixture:
            mock_urlopen().read.return_value = fixture.read()

        eztv_client = eztvit.EztvIt()
        eztv_client.get_episodes_by_id = mock.MagicMock()

        eztv_client.get_episodes('Suits')
        eztv_client.get_episodes_by_id.assert_called_with(495)

        # Check that we requested the homepage.
        request = self._get_request_from_mock(mock_urlopen)
        self.assertIn('WebKit', request.get_header('User-agent'))
        self.assertEquals(request.get_full_url(), 'https://eztv.ch/')
        self.assertEquals(request.get_method(), 'GET')

        # Check that we didn't make any other HTTP requests. We subtract one
        # because invoking the mock in order to assign the "read" return value
        # causes the call-count to increase by one.
        self.assertEquals(mock_urlopen.call_count - 1, 1)

    @mock.patch('urllib2.urlopen')
    def test_suits_via_show_id(self, mock_urlopen):
        # Mock urllib2 to return the episodes of the awesome TV show "Suits".
        with open('tests/fixtures/suits.html') as fixture:
            mock_urlopen().read.return_value = fixture.read()

        # Fetch the dictionary that represents all of the episodes of "Suits".
        suits = eztvit.EztvIt().get_episodes_by_id(495)

        # Ensure we're dealing with exactly dictionaries, not defaultdicts or
        # some other subclass of dict.
        self.assertEquals(type(suits), dict)
        for episodes in suits.values():
            self.assertEquals(type(episodes), dict)

        # Check the four seasons have the correct number of episodes.
        self.assertEquals(len(suits[1]), 12 - 1 - 1) # Epi. 6, 10 are missing.
        self.assertEquals(len(suits[2]), 16)
        self.assertEquals(len(suits[3]), 16)
        self.assertLessEqual(len(suits[4]), 10)

        # Test that "S04E06" has 2 episodes, in a particular order, with the
        # correct magnet links.
        suits_4x06 = suits[4][6]
        self.assertEquals(len(suits_4x06), 2)

        self.assertEquals(suits_4x06[0]['release'],
                          "Suits S04E06 REPACK HDTV x264-KILLERS")
        self.assertIn('magnet:?xt=urn:btih:D4JVVOTZ3YNAYO',
                      suits_4x06[0]['download']['magnet'])

        self.assertEquals(suits_4x06[1]['release'],
                          "Suits S04E06 HDTV x264-KILLERS")
        self.assertIn('magnet:?xt=urn:btih:VNL5SUXHIMCODE',
                      suits_4x06[1]['download']['magnet'])

        # Test that "1x11" has 1 episode.
        suits_1x11 = suits[1][11]
        self.assertEquals(len(suits_1x11), 1)

        self.assertEquals(suits_1x11[0]['release'],
                          "Suits 1x11 (HDTV-LOL) [VTV]")
        self.assertIn('magnet:?xt=urn:btih:6AD3E1D56CBA16',
                      suits_1x11[0]['download']['magnet'])

        # Check that we made an appropriate HTTP request to get this page.
        request = self._get_request_from_mock(mock_urlopen)
        self.assertIn('WebKit', request.get_header('User-agent'))
        self.assertEquals(request.get_full_url(), 'https://eztv.ch/search/')
        self.assertEquals(request.get_method(), 'POST')
        self.assertEquals(request.get_data(),
                          "SearchString1=&SearchString=495&Search=Search")

        # Check that we didn't make any other HTTP requests. We subtract one
        # because invoking the mock in order to assign the "read" return value
        # causes the call-count to increase by one.
        self.assertEquals(mock_urlopen.call_count - 1, 1)

    @mock.patch('urllib2.urlopen')
    def test_fringe_via_show_id(self, mock_urlopen):
        # Mock urllib2 to return the episodes of the awesome TV show "Fringe".
        with open('tests/fixtures/fringe.html') as fixture:
            mock_urlopen().read.return_value = fixture.read()

        # Fetch the dictionary that represents all of the episodes of "Fringe".
        fringe = eztvit.EztvIt().get_episodes_by_id(101)

        # Ensure we're dealing with exactly dictionaries, not defaultdicts or
        # some other subclass of dict.
        self.assertEquals(type(fringe), dict)
        for episodes in fringe.values():
            self.assertEquals(type(episodes), dict)

        # Check the four seasons have the correct number of episodes.
        self.assertEquals(len(fringe[1]), 20)
        self.assertEquals(len(fringe[2]), 23 - 1 - 1) # Epi. 11, 12 are missing.
        self.assertEquals(len(fringe[3]), 22 - 1) # Epi. 20 is missing.
        self.assertEquals(len(fringe[4]), 22)
        self.assertEquals(len(fringe[5]), 13)

    @mock.patch('urllib2.urlopen')
    def test_shows_list(self, mock_urlopen):
        # Mock urllib2 to return the homepage.
        with open('tests/fixtures/homepage.html') as fixture:
            mock_urlopen().read.return_value = fixture.read()

        # Fetch the dictionary that represents all of available shows.
        shows = eztvit.EztvIt().get_shows()

        self.assertEquals(shows[495], 'Suits')
        self.assertEquals(shows[101], 'Fringe')
        # Check the "The" has come back to the beginning.
        self.assertEquals(shows[23], 'The Big Bang Theory')
