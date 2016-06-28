import mock
import unittest
import eztvit
import urllib3

class TestEztvIt(unittest.TestCase):
    def _get_request_from_mock(self, mock_poolmanager, call_number=0):
        return mock_poolmanager().request.call_args_list[call_number][0]

    def _get_headers_from_mock(self, mock_poolmanager, call_number=0):
        # Google a better way to do this when I get a chance.
        return dict([mock_poolmanager().headers.__setitem__.call_args_list[call_number][0]])

    @mock.patch('urllib3.PoolManager')
    def test_suits_via_show_name(self, mock_poolmanager):
        with open('tests/fixtures/homepage.html') as fixture:
            mock_poolmanager().request.return_value = urllib3.response.HTTPResponse(fixture.read())

        eztv_client = eztvit.EztvIt()
        eztv_client.get_episodes_by_id = mock.MagicMock()

        eztv_client.get_episodes('Suits')
        eztv_client.get_episodes_by_id.assert_called_with(495)

        # Check that we requested the homepage.
        (method, url) = self._get_request_from_mock(mock_poolmanager)
        self.assertEquals(url, 'https://eztv.yt/')
        self.assertEquals(method, 'GET')

        headers = self._get_headers_from_mock(mock_poolmanager)
        self.assertEquals(len(headers), 1)
        self.assertIn('WebKit', headers['User-Agent'])

        # Check that we didn't make any other HTTP requests.
        self.assertEquals(mock_poolmanager().request.call_count, 1)

    @mock.patch('urllib3.PoolManager')
    def test_suits_via_show_id(self, mock_poolmanager):
        # Mock urllib2 to return the episodes of the awesome TV show "Suits".
        with open('tests/fixtures/suits.html') as fixture:
            mock_poolmanager().request.return_value = urllib3.response.HTTPResponse(fixture.read())

        # Fetch the dictionary that represents all of the episodes of "Suits".
        suits = eztvit.EztvIt().get_episodes_by_id(495)

        # Ensure we're dealing with exactly dictionaries, not defaultdicts or
        # some other subclass of dict.
        self.assertEquals(type(suits), dict)
        for episodes in suits.values():
            self.assertEquals(type(episodes), dict)

        # Check the four seasons have the correct number of episodes.
        self.assertEquals(len(suits[1]), 1) # Most episodes are missing.
        self.assertEquals(len(suits[2]), 16)
        self.assertEquals(len(suits[3]), 16)
        self.assertLessEqual(len(suits[4]), 16)

        # Test that "S04E06" has 2 episodes, in a particular order, with the
        # correct magnet links.
        suits_4x06 = suits[4][6]
        self.assertEquals(len(suits_4x06), 2)

        self.assertEquals(suits_4x06[0]['release'],
                          "Suits S04E06 REPACK HDTV x264-KILLERS [eztv]")
        self.assertIn('magnet:?xt=urn:btih:D4JVVOTZ3YNAYO',
                      suits_4x06[0]['download']['magnet'])

        self.assertEquals(suits_4x06[1]['release'],
                          "Suits S04E06 HDTV x264-KILLERS [eztv]")
        self.assertIn('magnet:?xt=urn:btih:VNL5SUXHIMCODE',
                      suits_4x06[1]['download']['magnet'])

        # Check that we made an appropriate HTTP request to get this page.
        (method, url) = self._get_request_from_mock(mock_poolmanager)
        self.assertEquals(url, 'https://eztv.yt/shows/495/')
        self.assertEquals(method, 'GET')

        headers = self._get_headers_from_mock(mock_poolmanager)
        self.assertEquals(len(headers), 1)
        self.assertIn('WebKit', headers['User-Agent'])

        # Check that we didn't make any other HTTP requests.
        self.assertEquals(mock_poolmanager().request.call_count, 1)

    @mock.patch('urllib3.PoolManager')
    def test_fringe_via_show_id(self, mock_poolmanager):
        # Mock urllib2 to return the episodes of the awesome TV show "Fringe".
        with open('tests/fixtures/fringe.html') as fixture:
            mock_poolmanager().request.return_value = urllib3.response.HTTPResponse(fixture.read())

        # Fetch the dictionary that represents all of the episodes of "Fringe".
        fringe = eztvit.EztvIt().get_episodes_by_id(101)

        # Ensure we're dealing with exactly dictionaries, not defaultdicts or
        # some other subclass of dict.
        self.assertEquals(type(fringe), dict)
        for episodes in fringe.values():
            self.assertEquals(type(episodes), dict)

        # Check the four seasons have the correct number of episodes (season 1 and 2 are missing).
        self.assertEquals(len(fringe[3]), 15)
        self.assertEquals(len(fringe[4]), 22)
        self.assertEquals(len(fringe[5]), 13)

    @mock.patch('urllib3.PoolManager')
    def test_shows_list(self, mock_poolmanager):
        # Mock urllib2 to return the homepage.
        with open('tests/fixtures/homepage.html') as fixture:
            mock_poolmanager().request.return_value = urllib3.response.HTTPResponse(fixture.read())

        # Fetch the dictionary that represents all of available shows.
        shows = eztvit.EztvIt().get_shows()

        self.assertEquals(shows[495], 'Suits (2011)')
        self.assertEquals(shows[101], 'Fringe (2008)')
        # Check the "The" has come back to the beginning.
        self.assertEquals(shows[23], 'The Big Bang Theory (2007)')
