import unicodecsv
import argparse
import sys
import json
import copy

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

    topic_ids = ['crime_s1', 'crime_s2', 'crime_s3', 'econ_s1', 'econ_s2', 'econ_s3', 'edu_s1', 'edu_s2', 'edu_s3', 'env_s1', 'env_s2', 'env_s3', 'foreign_s1', 'foreign_s2', 'foreign_s3', 'heal_s1', 'heal_s2', 'heal_s3', 'imi_s1', 'imi_s2', 'imi_s3', 'ineq_s1', 'ineq_s2', 'ineq_s3', 'jobs_s1', 'jobs_s2', 'jobs_s3', 'living_s1', 'living_s2', 'living_s3', 'reform_s1', 'reform_s2', 'reform_s3', 'tax_s1', 'tax_s2', 'tax_s3', 'welfare_s1', 'welfare_s2', 'welfare_s3']
    priority_ids = ['priority_0', 'priority_1', 'priority_2', 'priority_3', 'priority_4', 'priority_5', 'priority_6', 'priority_7', 'priority_8', 'priority_9', 'priority_10', 'priority_11', 'priority_12', 'priority_13']

    input_fields = ['id', 'age', 'gender', 'location', 'observation_index', 'overall_party_match']
    input_fields += topic_ids
    input_fields += priority_ids

    location_fields = ['lat', 'lon', 'constituency_name', 'constituency_mapit_id']
    location_csv_fields = ['lat', 'lon', 'id', 'constituency_name', 'constituency_mapit_id']

    output_fields = input_fields + location_fields

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
            row_copy['lat'] = location['lat']
            row_copy['lon'] = location['lon']
            row_copy['constituency_name'] = location['constituency_name']
            row_copy['constituency_mapit_id'] = location['constituency_mapit_id']
        output_rows.append(row_copy)
        sys.stdout.write(".")

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        writer = unicodecsv.DictWriter(f, output_fields)
        writer.writeheader()
        writer.writerows(output_rows)
