[![Build Status](https://travis-ci.org/jaysh/eztvit-python.svg?branch=master)](https://travis-ci.org/jaysh/eztvit-python)

eztv.it Python Connector
=============

A Simple API that allows anyone to retrieve the list of shows that EZTV has, and print information about episodes and seasons a particular season has to offer.

# Installation from PyPi

    sudo pip install eztvit

# Building the project

    python setup.py sdist

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