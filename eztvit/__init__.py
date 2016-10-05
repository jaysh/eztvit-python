#!/usr/bin/env python
"""
Python interface for EZTV.

Works by screen-scraping the homepage and show pages, but depending as little
on the names of elements or structure of the DOM as possible.
"""

__version__ = "3.3.1"

import bs4
import json
import re
import collections
import urlparse
import urllib3
import hashlib
import urllib3.contrib.pyopenssl

urllib3.contrib.pyopenssl.inject_into_urllib3()

SCHEME = 'https'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux i686) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Ubuntu Chromium/30.0.1599.114 '
                  'Chrome/30.0.1599.114 Safari/537.36'
}
EZTV_DOMAIN = 'eztv.ag'

class EztvIt(object):
    """EZTV Client

    Example usage:

    import eztvit
    eztvit.EztvIt().get_episodes('Suits')
    """

    def __init__(self):
        self.shows_list = None

        self.http = urllib3.PoolManager()
        self.http.headers['User-Agent'] = HEADERS['User-Agent']

    def _get_episodes_page_html(self, show_id):
        """Fetch the shows page.

        This simulates selecting a show from the homepage dropdown, and click
        on the "Search" button.
        """
        response = self.http.request(
            'GET',
            SCHEME + '://' + EZTV_DOMAIN + '/search/?q1=&q2={show_id}&search=Search'.format(show_id=show_id)
        )

        return response.data

    def _get_shows_dropdown_javascript(self):
        """Fetch the homepage."""
        response = self.http.request('GET', SCHEME + '://' + EZTV_DOMAIN + '/js/search_shows1.js')

        return response.data

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

        javascript_source = self._get_shows_dropdown_javascript()
        # Search for the first assignment of a list of things. We take that as the shows list.
        shows_list_match = re.search(r'=\s*(\[.+?\])', javascript_source)
        if not shows_list_match:
            raise RuntimeError("Cannot find shows list in Javascript source")

        parsed_shows = json.loads(shows_list_match.group(1))

        # The shows that we have parsed.
        self.shows_list = {}

        for parsed_show in parsed_shows:
            original_name = parsed_show['text']
            try:
                show_id = int(parsed_show['id'])
            except ValueError:
                # Skip this show and move on to the next one.
                continue

            # EZTV have a neat trick where they place the "The " of a show at
            # the end of the string, but also append the year. So "The Big
            # Bang Theory" will become "Big Bang Theory, The (2007)". We put
            # it at the beginning in order to normalize it to make it more
            # intuitive to lookup against.
            match = re.search(r'(.+?), (The)\s*(\(\d+\))?', original_name)
            if match:
                # Only keep the truthy name parts.
                name_parts = filter(None, [match.group(2), match.group(1), match.group(3)])
                normalized_name = ' '.join(name_parts)
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

        match = filter(lambda candidate: candidate.lower().startswith(show_name.lower()), shows.values())

        # If there is more than one match
        if len(match) > 1:
           raise Exception("More than one partial match for " + show_name)

        match = match[0]

        if not match:
            raise KeyError("Show not found")

        (show_id, ) = [k for k, v in shows.iteritems() if v == match]

        return self.get_episodes_by_id(show_id)

    def get_episodes_by_id(self, show_id):
        """Get the episodes for a show based on its ID."""
        parsed = bs4.BeautifulSoup(self._get_episodes_page_html(show_id), "lxml")

        # First, we need to locate the table that contains the "Television
        # Show Releases".
        tv_releases_title = parsed.find(text=lambda t: 'EZTV Series: Latest Torrents' in t)
        if not tv_releases_title:
            raise RuntimeError("Unable to locate the table that contains the "
                               "list of releases")

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
        release_anchors = parsed.find_all('a', text=episode_code_regex)

        for anchor in release_anchors:
            # The anchor itself will be contained by a <tr> (i.e. the whole
            # row of the table). This ensures we're look at precisely one
            # episode (row) at a time.
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
            torrent_links = row.find_all(href=re.compile(r'\.torrent$'))
            if torrent_links:
                # Scheme-relative links are pretty useless in the output, so
                # we substitute any missing schemes for the way we accessed
                # this page in the first place (e.g. if we accessed it over
                # https, we use https as the default).
                hrefs = (torrent_link.get('href') for torrent_link in torrent_links)
                links['torrents'] = [urlparse.urlparse(href, SCHEME).geturl() for href in hrefs]

            # Find the anchor that looks like it has a title for the filesize.
            filesize_regex = re.compile(r'([\d\.]+) (MB|GB|B)')
            filesize_anchor = row.find(title=filesize_regex)
            filesize_mb = None

            if filesize_anchor:
                # Get the size and the units
                filesize_match = filesize_regex.search(filesize_anchor.get('title'))
                assert filesize_match, "Extract the filesize from the title"

                # Parse the human MB/GB into a universal megabytes format.
                factors = {'GB': 1024, 'MB': 1, 'B': 0}
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

            assert season is not None, "Find the season number"
            assert episode is not None, "Find the episode number"

            shows[season][episode].append({
                'release': anchor.text,
                'download': links,
                'size_mb': filesize_mb,
            })

        # Return a dict, not a defaultdict.
        return dict(
            dict((season, dict(episodes)) for
                 (season, episodes) in shows.iteritems())
        )
