import unicodecsv
import argparse
import sys
import json
import copy

from constants import (
    USER_FIELDS,
    TOPIC_IDS,
    PRIORITY_IDS,
    LOCATION_FIELDS,
    VOTE_MATCH_FIELDS
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Adds vote matches to CSV")
    parser.add_argument(
        'input_csv',
        type=argparse.FileType('r'),
        help="Path to users CSV data file to load"
    )
    parser.add_argument(
        'matches_csv',
        type=argparse.FileType('r'),
        help="Path to vote match CSV data file to load"
    )
    parser.add_argument(
        'output_csv',
        type=str,
        help="Path to CSV file to output"
    )
    args = parser.parse_args()

    input_fields = USER_FIELDS
    input_fields += TOPIC_IDS
    input_fields += PRIORITY_IDS
    input_fields += LOCATION_FIELDS

    matches_csv_fields = ['user_id'] + list(VOTE_MATCH_FIELDS)

    output_fields = input_fields + VOTE_MATCH_FIELDS

    output_rows = []

    matches_reader = unicodecsv.DictReader(args.matches_csv, matches_csv_fields)
    matches_by_user_id = {row['user_id']: row for row in matches_reader}

    print "There are {0} users with matches".format(len(matches_by_user_id))

    print "Processing"
    reader = unicodecsv.DictReader(args.input_csv, input_fields)
    for row in reader:
        row_copy = copy.deepcopy(row)
        match = matches_by_user_id.get(row['id'])
        for column in VOTE_MATCH_FIELDS:
            row_copy[column] = ''
        if match:
            for column in VOTE_MATCH_FIELDS:
                row_copy[column] = match[column]
        output_rows.append(row_copy)
        sys.stdout.write(".")

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        writer = unicodecsv.DictWriter(f, output_fields)
        writer.writeheader()
        writer.writerows(output_rows)
