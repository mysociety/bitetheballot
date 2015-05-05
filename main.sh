#!/bin/bash
set -e

# Runs through all of the scripts necessary in order to go from downloaded
# json file to output CSV file

# Assumes that you've put a file called bitetheballot.json into the current
# directory.

# Works in a scratch directory called /tmp/bitetheballot and then deletes
# that folder afterwards.

if [ -f bitetheballot.json ]
then
    echo "Creating temp directory"
    mkdir /tmp/bitetheballot

    # Split up the file
    echo "Spliting up JSON file"
    cat bitetheballot.json | jq .users > /tmp/bitetheballot/bitetheballot-users.json
    cat bitetheballot.json | jq .locations > /tmp/bitetheballot/bitetheballot-locations.json
    cat bitetheballot.json | jq .priorities > /tmp/bitetheballot/bitetheballot-priorities.json

    # Start the pythons
    source ../virtualenv-bitetheballot/bin/activate

    echo "Turning locations into a CSV"
    python process_locations_to_csv.py /tmp/bitetheballot/bitetheballot-locations.json /tmp/bitetheballot/bitetheballot-locations.csv

    echo "Processing locations through MapIt - this may take a while"
    python lookup_locations_on_mapit.py /tmp/bitetheballot/bitetheballot-locations.csv /tmp/bitetheballot/bitetheballot-locations-with-constituencies.csv

    echo "Turning users in to a CSV"
    python process_users_to_csv.py /tmp/bitetheballot/bitetheballot-users.json /tmp/bitetheballot/bitetheballot-users.csv

    echo "Adding priorities to user CSV"
    python add_priorities_to_csv.py /tmp/bitetheballot/bitetheballot-users.csv /tmp/bitetheballot/bitetheballot-priorities.json /tmp/bitetheballot/bitetheballot-users-with-priorities.csv

    echo "Adding locations to user CSV"
    python add_locations_to_csv.py /tmp/bitetheballot/bitetheballot-users-with-priorities.csv /tmp/bitetheballot/bitetheballot-locations-with-constituencies.csv /tmp/bitetheballot/bitetheballot-users-with-priorities-and-locations.csv

    echo "Cleaning up"
    cp /tmp/bitetheballot/bitetheballot-users-with-priorities-and-locations.csv bitetheballot.csv
    rm -rf /tmp/bitetheballot
else
    echo "bitetheballot.json not found"
    exit 1
fi
