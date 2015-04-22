import unicodecsv
import json
import argparse

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

    locations = json.load(args.json_file)

    rows = []
    for id, location in locations.items():
        row = {
            'id': id,
            'lat': location['l'][0],
            'lon': location['l'][1]
        }
        rows.append(row)

    with open(args.output_csv, 'wb') as f:
        writer = unicodecsv.DictWriter(f, ['id', 'lat', 'lon'])
        writer.writeheader()
        writer.writerows(rows)
