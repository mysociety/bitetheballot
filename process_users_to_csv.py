import unicodecsv
import json
import argparse
import datetime
import sys
from dateutil.relativedelta import relativedelta

import utils
from constants import TOPIC_IDS, USER_FIELDS

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Converts JSON to CSV")
    parser.add_argument(
        'json_file',
        type=argparse.FileType('r'),
        help="Path to JSON data file to load"
    )
    parser.add_argument(
        'output_csv',
        type=str,
        help="Path to csv file to output"
    )
    args = parser.parse_args()

    users = json.load(args.json_file)

    now = datetime.datetime.utcnow()

    rows = []
    print "Processing:"
    for id, user in users.items():
        row = {
            'id': id,
            'age': '',
            'gender': '',
            'location': ''
        }

        # Some users aren't an object at all
        if user == "false":
            rows.append(row)
            continue

        if user.get('locationname') is not None:
            row['location'] = user['locationname']
        if user.get('gender') is not None:
            row['gender'] = user['gender']
        if user.get('dob') is not None:
            try:
                date_of_birth = datetime.datetime.utcfromtimestamp(int(user['dob']))
                row['age'] = relativedelta(now, date_of_birth).years
            except Exception:
                print "Couldn't parse age: {0} into a date".format(user['dob'])
        for topic_id in TOPIC_IDS:
            row[topic_id] = ""
        if user.get('decisions') is not None:
            for decision in user['decisions']:
                decision = utils.clean_decision(decision, user['decisions'])
                if decision is None:
                    continue
                topic_id = "{0}_{1}".format(decision['topic'], decision['statement'])
                row[topic_id] = decision['position']
        rows.append(row)
        sys.stdout.write('.')

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        fields = USER_FIELDS
        fields += TOPIC_IDS
        writer = unicodecsv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)
