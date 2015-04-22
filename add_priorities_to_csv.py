import unicodecsv
import argparse
import sys
import json
import copy

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Converts JSON to CSV")
    parser.add_argument(
        'input_csv',
        type=argparse.FileType('r'),
        help="Path to users CSV data file to load"
    )
    parser.add_argument(
        'input_json',
        type=argparse.FileType('r'),
        help="Path to priorities JSON data file to load"
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

    output_fields = input_fields + priority_ids

    priorities_json = json.load(args.input_json)

    output_rows = []

    print "Processing"
    reader = unicodecsv.DictReader(args.input_csv, input_fields)
    for row in reader:
        row_copy = copy.deepcopy(row)
        priorities = priorities_json.get(row['id'])
        if priorities and priorities.get('topics'):
            for topic in priorities['topics']:
                topic_priority_id = 'priority_{0}'.format(topic['position'])
                row_copy[topic_priority_id] = topic['slug']
        output_rows.append(row_copy)
        sys.stdout.write(".")

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        writer = unicodecsv.DictWriter(f, output_fields)
        writer.writeheader()
        writer.writerows(output_rows)
