#!/usr/bin/env python
"""
Python interface for EZTV.

Works by screen-scraping the homepage and show pages, but depending as little
on the names of elements or structure of the DOM as possible.
"""

__version__ = "2.1"

import bs4
import re
import collections
import urlparse
import urllib
import urllib2

SCHEME = 'https'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Ubuntu Chromium/30.0.1599.114 '
                  'Chrome/30.0.1599.114 Safari/537.36'
}

class EztvIt(object):
    """EZTV.it Client

    Example usage:

    import eztvit
    eztvit.EztvIt().get_episodes('Suits')
    """

    def __init__(self):
        self.shows_list = None

    def _get_episodes_page_html(self, show_id):
        """Fetch the shows page.

        This simulates selecting a show from the homepage dropdown, and click
        on the "Search" button.
        """
        data = [('SearchString1', ''),    # We don't "type" search query itself.
               ('SearchString', show_id), # We do supply a show list.
               ('Search', 'Search')]      # Search button.
        request = urllib2.Request(
            url=SCHEME + '://eztv.ch/search/',
            headers=HEADERS,
            data=urllib.urlencode(data),
        )

        return urllib2.urlopen(request).read()

    def _get_homepage_html(self):
        """Fetch the homepage."""
        request = urllib2.Request(url=SCHEME + '://eztv.ch/', headers=HEADERS)

        return urllib2.urlopen(request).read()

    def get_shows(self):
        """Get the list of shows on offer.

        Returns a dict, with the show ID as the key, and the show name as the
        value. All show names are normalized, for example if a show ends in
        "The, ", it's placed at the start.

        For performance, the shows are cached in memory so subsequent calls
        are fast.
        """
        # Check the cache.
        if self.shows_list is not None:
            return self.shows_list

        parsed = bs4.BeautifulSoup(self._get_homepage_html())
        shows_select = parsed.find('select', attrs={'name': 'SearchString'})
        if not shows_select:
            raise RuntimeError("Cannot find dropdown called SearchString"
                               " with the shows in on the homepage.")

        # The shows that we have parsed.
        self.shows_list = {}

        shows_options = shows_select.find_all('option')
        for option in shows_options:
            original_name = option.string
            try:
                show_id = int(option['value'])
            except ValueError:
                # Skip this show and move on to the next one.
                continue

            # EZTV have a neat trick where they place the "The " of a show at
            # the end of the string. So "The Big Bang Theory" will become "Big
            # Bang Theory, The". We put it at the beginning in order to
            # normalize it to make it more intuitive to lookup against.
            if original_name[-5:] == ", The":
                normalized_name = "The " + original_name[0:-5]
            else:
                normalized_name = original_name

            self.shows_list[show_id] = normalized_name

        return self.shows_list

    def get_episodes(self, show_name):
        """Get the episodes for a show by name.

        This has an additional overhead of having to request the homepage.
        Where possible, you should retrieve the show ID yourself and save it,
        then call get_episodes_by_id directly to remove the overhead.
        """
        shows = self.get_shows()
        if show_name not in shows.values():
            raise KeyError("Show not found")

        (show_id, ) = [k for k, v in shows.iteritems() if v == show_name]

        return self.get_episodes_by_id(show_id)

    def get_episodes_by_id(self, show_id):
        """Get the episodes for a show based on its ID."""
        parsed = bs4.BeautifulSoup(self._get_episodes_page_html(show_id))

        # First, we need to locate the table that contains the "Television
        # Show Releases".
        tv_releases_title = parsed.find(
            text=lambda t: t.strip() == 'Television Show Releases')
        if not tv_releases_title:
            raise RuntimeError("Unable to locate the table that contains the "
                               "list of releases")

        shows_table = tv_releases_title.find_parent('table')
        if not shows_table:
            raise RuntimeError("The structure of the website has changed: "
                               "the title we found is not longer within the "
                               "table that contains the list of releases.")

        # Different release authors choose different formats, so we try to
        # cater for them all.
        episode_codes = [
            r'S(\d{1,2})E(\d{1,2})', # e.g. S02E16
            r'(\d{1,2})x(\d{1,2})', # e.g. 2x02
        ]
        # We build the general regex by ensuring any if the release formats
        # that match, must do with surrounding whitespace. This gives the
        # maximum chance that we're matching the episode code and not some
        # other part of the title.
        episode_code_regex = re.compile(r'\s' + '|'.join(episode_codes) + r'\s')

        # We build a structure of the form shows[season][episode] = [matching
        # links] (since one episode may have multiple releases by different
        # authors or different quality).
        shows = collections.defaultdict(lambda: collections.defaultdict(list))

        # Attempt to locate all of the hyperlinks within the shows table that
        # contain, what appear to be, episode codes. The object here is not to
        # tightly couple ourself to EZTVs DOM (i.e. not specifically look for
        # an anchor within a td). This enables them to reasonably refactor the
        # page, provided the end result is still a <table> (which it should
        # be, since this is tabular data, after all) and we'll stil have no
        # real issues matching episode information.
        release_anchors = shows_table.find_all('a', text=episode_code_regex)

        for anchor in release_anchors:
            # The anchor itself will be contained by a <tr> (i.e. the whole
            # row of the table). Find this parent of ours ensures we're look
            # at precisely one episode at a time.
            row = anchor.find_parent('tr')
            if not row:
                raise RuntimeError("The episode anchor was not contained "
                                   "inside a <tr>")

            # Matching download links.
            links = {}

            # A magnet link is simply a link that has "magnet" as the protocol
            # (i.e. it begins with "magnet:").
            magnet_link = row.find(href=re.compile(r'^magnet:'))
            if magnet_link:
                links['magnet'] = magnet_link.get('href')

            # We consider a link to point to a torrent if it ends in
            # ".torrent". Note, this isn't foolproof - i.e.
            # "http://www.google.com/?.torrent" would trick this into
            # matching.
            torrent_link = row.find(href=re.compile(r'\.torrent$'))
            if torrent_link:
                # Scheme-relative links are pretty useless in the output, so
                # we substitute any missing schemes for the way we accessed
                # this page in the first place (e.g. if we accessed it over
                # https, we use https as the default).
                href = torrent_link.get('href')
                links['torrent'] = urlparse.urlparse(href, SCHEME).geturl()

            # Find the anchor that looks like it has a title for the filesize.
            filesize_regex = re.compile(r'([\d\.]+) (MB|GB)')
            filesize_anchor = row.find(title=filesize_regex)
            # Get the size and the units
            filesize_match = filesize_regex.search(filesize_anchor.get('title'))
            assert filesize_match, "Extract the filesize from the title"

            # Parse the human MB/GB into a universal megabytes format.
            factors = {'GB': 1024, 'MB': 1}
            filesize_units = filesize_match.group(2)
            assert filesize_units in factors
            # Convert it to a reasonably-readable megabyte-size.
            filesize_mb = int(
                float(filesize_match.group(1)) * factors[filesize_units])

            season = None
            episode = None
            for release_format in episode_codes:
                release_match = re.search(release_format, anchor.text)
                if release_match:
                    season = int(release_match.group(1))
                    episode = int(release_match.group(2))

            assert season and episode, "Find the season/episode numbers"
            shows[season][episode].append({
                'release': anchor.text,
                'download': links,
                'size_mb': filesize_mb,
            })

        # Return a dict, not a defaultdict.
        return dict(
            dict((season, dict(episodes))
            for (season, episodes) in shows.iteritems())
        )
