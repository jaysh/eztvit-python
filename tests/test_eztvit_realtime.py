import unittest
import eztvit

class TestEztvItRealTime(unittest.TestCase):
    def setUp(self):
        print "Running tests that connect to EZTVs live servers..."

    def test_suits(self):
        suits = eztvit.EztvIt().get_episodes('Suits')

        # Check the four seasons have the correct number of episodes.
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
