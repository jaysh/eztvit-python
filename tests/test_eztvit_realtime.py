import unittest
import eztvit

class TestEztvItRealTime(unittest.TestCase):
    def setUp(self):
        print "Running tests that connect to EZTVs live servers..."

    def test_suits(self):
        suits = eztvit.EztvIt().get_episodes('Suits')

        # Check the four seasons have the correct number of episodes.
        self.assertEquals(len(suits[1]), 12 - 1 - 1) # Epi. 6, 10 are missing.
        self.assertEquals(len(suits[2]), 16)
        self.assertEquals(len(suits[3]), 16)

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
                          u"Suits 1x11 (HDTV-LOL)")
        self.assertIn('magnet:?xt=urn:btih:6AD3E1D56CBA16',
                      suits_1x11[0]['download']['magnet'])
