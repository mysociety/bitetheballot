import unicodecsv
import json
import argparse
import datetime
import sys
from dateutil.relativedelta import relativedelta

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

    topic_ids = ['crime_s1', 'crime_s2', 'crime_s3', 'econ_s1', 'econ_s2', 'econ_s3', 'edu_s1', 'edu_s2', 'edu_s3', 'env_s1', 'env_s2', 'env_s3', 'foreign_s1', 'foreign_s2', 'foreign_s3', 'heal_s1', 'heal_s2', 'heal_s3', 'imi_s1', 'imi_s2', 'imi_s3', 'ineq_s1', 'ineq_s2', 'ineq_s3', 'jobs_s1', 'jobs_s2', 'jobs_s3', 'living_s1', 'living_s2', 'living_s3', 'reform_s1', 'reform_s2', 'reform_s3', 'tax_s1', 'tax_s2', 'tax_s3', 'welfare_s1', 'welfare_s2', 'welfare_s3']

    now = datetime.datetime.utcnow()

    rows = []
    print "Processing:"
    for id, user in users.items():
        row = {
            'id': id,
            'age': '',
            'gender': '',
            'location': '',
            'observation_index': '',  # TODO - what is this in the data?
            'overall_party_match': '',  # TODO - where is this in the data?
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
        for topic_id in topic_ids:
            row[topic_id] = ""
        if user.get('decisions') is not None:
            for decision in user['decisions']:
                # Some of the decisions are (annoyingly) a different structure
                # to the rest
                if isinstance(decision, basestring):
                    decision = user['decisions'][decision]
                # Some decisions are null objects so skip those
                if decision is None:
                    continue
                topic_id = "{0}_{1}".format(decision['topic'], decision['statement'])
                # TODO - is position the right thing here? What about weight?
                row[topic_id] = decision['position']
        rows.append(row)
        sys.stdout.write('.')

    print "\nSaving"
    with open(args.output_csv, 'wb') as f:
        fields = ['id', 'age', 'gender', 'location', 'observation_index', 'overall_party_match']
        fields += topic_ids
        writer = unicodecsv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)
