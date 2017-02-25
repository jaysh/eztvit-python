Latest version: 3.3.2 - **February 2017** | [![Build Status](https://travis-ci.org/jaysh/eztvit-python.svg?branch=master)](https://travis-ci.org/jaysh/eztvit-python)

EZTV API
=============

Simple wrapper for EZTV that enables you to search for shows, and pull up show information in a structured and reliable format.

Changelog (last 24 months)
=============

*February 2017*:
- When pulling up shows by name, look for an exact match before performing a prefix search to find a best match.

*October 2016*:
- New domain (eztv.ag)
- Search box now uses a typeahead with the show list populated via Javascript
- Use search results page to locate episodes rather than show page due to show page specific bugs

*August 2016*:
- EZTV has split the filesize into a dedicated column
- Revert back to the search rather than show page due to bugs on show pages (some filesizes missing)

*June 2016*:
- New domain (eztv.yt)
- Adapt to new name of search box (thanks to [anthonygclark](https://github.com/anthonygclark))
- Make show lookup a partial match due to addition of the show year to all shows (previously only some shows had the year) (thanks to [anthonygclark](https://github.com/anthonygclark))

*October 2015*:
- Use urllib3 instead of urllib2 for better connectivity over SSL (including CloudFlare'd websites that use SNI)

*September 2015*:
- Update text we look for in the table header

*August 2015*:
- New domain (eztv.ag)
- Small scraping updates due to page structure changes

# Installation from PyPi

    sudo pip install eztvit

# Building the project for release and uploading to PyPi

    python setup.py sdist upload

# Usage 

    $ python
    Python 2.7.6 (default, Mar 22 2014, 22:59:56) 
    [GCC 4.8.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import eztvit, pprint
    >>> eztvit.EztvIt().get_shows().values()[0:5]
    [u'24', u'30 Rock', u'90210', u'According to Jim', u'The Amazing Race']
    >>> pprint.pprint(eztvit.EztvIt().get_episodes('Game of Thrones'))
    {
        1: {
            1: [
                {'download':
                    {
                        'magnet': 'magnet:?xt=urn:btih:BMUWPATF433OE...',
                        'torrent': 'http://...'
                    },
                    'release': u'Game of Thrones S01E01 720p HDTV x264-CTU',
                    'size_mb': 1495
                },
                ...
            ],
            ...
        }
        ...
    }

## Tests

The code ships with tests and some static HTML output to run against.

    $ python -m unittest tests.test_eztvit
    ...
    ----------------------------------------------------------------------
    Ran 3 tests in 0.294s

    OK

However, it's not entirely useful to *just* run the code against pre-defined HTML output, given that this won't reflect when EZTV modifies its pages.

As a result, there is one more test class that runs against the live website:

    $ python -m unittest tests.test_eztvit_realtime
    .
    ----------------------------------------------------------------------
    Ran 1 test in 3.481s

    OK

## Notes

It's built using Beautiful Soup to scrape the HTML pages. However, it's been written to be as adaptive to DOM changes as much as possible, by attempting to scrape what the use would be looking for with their eye, rather what class the `<table>` has.

For example, when scraping for shows, we seek out hyperlinks that contain strings of the format `S__E__` (e.g. S01E01) or `_x__` (1x11). Since it appears reasonable that the table of shows is represented by a `<table>` (since it's tabular data), we then scan up to the closest `<tr>` which is the containing row. In order to find the links, we simply examine all `<a>`s for a link that starts with `magnet:` - rather than relying on a link that has `class="magnet"` which will be more fragile in the long run.
