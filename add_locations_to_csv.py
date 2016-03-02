import unicodecsv
import argparse
import sys
import json
import copy

from constants import USER_FIELDS, TOPIC_IDS, PRIORITY_IDS, LOCATION_FIELDS

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Adds locations to CSV")
    parser.add_argument(
        'input_csv',
        type=argparse.FileType('r'),
        help="Path to users with priorities CSV data file to load"
    )
    parser.add_argument(
        'locations_csv',
        type=argparse.FileType('r'),
        help="Path to locations CSV data file to load"
    )
    parser.add_argument(
        'output_csv',
        type=str,
        help="Path to CSV file to output"
    )
    args = parser.parse_args()

    input_fields = list(USER_FIELDS)
    input_fields += list(TOPIC_IDS)
    input_fields += list(PRIORITY_IDS)

    print input_fields

    location_csv_fields = ['lat', 'lon', 'id', 'constituency_name', 'constituency_mapit_id']

    output_fields = input_fields + list(LOCATION_FIELDS)

    print output_fields

    output_rows = []

    location_reader = unicodecsv.DictReader(args.locations_csv, location_csv_fields)
    locations_by_user_id = {row['id']: row for row in location_reader}

    print "There are {0} users with locations".format(len(locations_by_user_id))

    print "Processing"
    reader = unicodecsv.DictReader(args.input_csv, input_fields)
    for row in reader:
        row_copy = copy.deepcopy(row)
        location = locations_by_user_id.get(row['id'])
        row_copy['lat'] = ''
        row_copy['lon'] = ''
        row_copy['constituency_name'] = ''
        row_copy['constituency_mapit_id'] = ''
        if location:
            print "found location"
            row_copy['lat'] = location['lat']
            row_copy['lon'] = location['lon']
            row_copy['constituency_name'] = location['constituency_name']
            row_copy['constituency_mapit_id'] = location['constituency_mapit_id']
        else:
            print "couldn't find location for {}".format(row['id'])
        output_rows.append(row_copy)
        sys.stdout.write(".")

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        writer = unicodecsv.DictWriter(f, output_fields)
        writer.writeheader()
        writer.writerows(output_rows)
