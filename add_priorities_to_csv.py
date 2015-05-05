import unicodecsv
import argparse
import sys
import json
import copy

from constants import PRIORITY_IDS, TOPIC_IDS, USER_FIELDS

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

    input_fields = list(USER_FIELDS)
    input_fields += list(TOPIC_IDS)

    output_fields = input_fields + list(PRIORITY_IDS)

    priorities_json = json.load(args.input_json)

    output_rows = []

    print "Processing"
    reader = unicodecsv.DictReader(args.input_csv, input_fields)
    for row in reader:
        row_copy = copy.deepcopy(row)
        priorities = priorities_json.get(row['id'])
        if priorities and priorities.get('topics'):
            for topic in priorities['topics']:
                if isinstance(topic, basestring):
                    topic = priorities['topics'][topic]
                topic_priority_id = 'priority_{0}'.format(topic['position'])
                row_copy[topic_priority_id] = topic['slug']
        output_rows.append(row_copy)
        sys.stdout.write(".")

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        writer = unicodecsv.DictWriter(f, output_fields)
        writer.writeheader()
        writer.writerows(output_rows)
