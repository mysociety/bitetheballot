#!/usr/bin/env python

import os
import unicodecsv as csv
import sys
from time import sleep

import requests
import requests_cache


# Setup the cache for Requests, so as to not hammer MapIt
REQUESTS_CACHE_PATH = os.path.join(os.path.dirname(__file__), "requests_cache")
if not os.path.exists(REQUESTS_CACHE_PATH):
    os.makedirs(REQUESTS_CACHE_PATH)
requests_cache.install_cache(os.path.join(REQUESTS_CACHE_PATH, "cache"))

AREA_TYPES = ("WMC",)
MAPIT_URL = "http://mapit.mysociety.org/point/4326/{{lon}},{{lat}}?types={types}".format(types=",".join(AREA_TYPES))
# How long to sleep between requests to MapIt, in seconds. Set to 0 to disable rate limiting.
SLEEP_INTERVAL = 0


def main():
    """
    Quick hacky script to update a CSV provided by Shelter with each property's
    local authority's 'ons' code from MapIt.
    Usage: ./mapit_lookup.py <input csv file> <output csv file>
    The output CSV file will be overwritten.
    """
    with open(sys.argv[1]) as infile, open(sys.argv[2], 'wb') as outfile:
        reader = csv.DictReader(infile)
        writer = None
        for row in reader:
            if not writer:
                keys = row.keys() + ["constituency_name", "constituency_mapit_id"]
                writer = csv.DictWriter(outfile, keys)
                writer.writerow({key: key for key in keys})
            lat, lon = row['lat'], row['lon']
            row['constituency_name'] = ""
            row['constituency_mapit_id'] = ""
            response = requests.get(MAPIT_URL.format(lat=lat, lon=lon))
            if response.status_code == 200:
                areas = {}
                try:
                    for mapit_id, area in response.json().items():
                        if area['type'] == 'WMC':
                            row['constituency_name'] = area['name']
                            row['constituency_mapit_id'] = mapit_id
                            break
                    if not row['constituency_name']:
                        print "Couldn't get council from URL {}".format(response.url)
                except ValueError:
                    # Requests raises a ValueError if the response is not json
                    # so we just skip looking up this row
                    pass
            writer.writerow(row)
            sys.stdout.write(".")
            sys.stdout.flush()
            if not response.from_cache and SLEEP_INTERVAL:
                sleep(SLEEP_INTERVAL)


if __name__ == '__main__':
    main()
