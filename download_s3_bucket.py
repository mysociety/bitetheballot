import os
import argparse
from progressbar import ProgressBar

import boto

from secrets import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

progress_bar = None


def print_progress(num_bytes, total_bytes):
    global progress_bar
    if progress_bar is None:
        progress_bar = ProgressBar(total_bytes)
        progress_bar.start()
    progress_bar.update(num_bytes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Adds locations to CSV")
    parser.add_argument(
        'bucket',
        type=str,
        help="S3 Bucket name"
    )
    parser.add_argument(
        'output_dir',
        type=str,
        help="Output directory for downloaded files. Will be created if it doesn't exist."
    )
    args = parser.parse_args()

    # Create the output folder if it doesn't exist
    if not os.path.exists(args.output_dir):
        print("Creating output directory because it doesn't exist.")
        os.mkdir(args.output_dir)

    # connect to the bucket
    conn = boto.connect_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    bucket = conn.get_bucket(args.bucket)

    # go through the list of files
    bucket_list = bucket.list()
    for l in bucket_list:
        # S3 doesn't care about directories, so l is a Key, which equates to
        # a full path from the top of the bucket to the folder we want, e.g.
        # 2015/08/29/2015-04-29T20:49:26Z_bitetheballot_backup/bitetheballot.json
        # We take this and save it as a timestamped version of the root file
        keyString = str(l.key)
        filename_parts = keyString.split("/")
        filename = filename_parts[-1]
        filetype = filename.split(".")[-1]
        if filetype == "json":
            timestamp_dirname = filename_parts[-2]
            timestamp = timestamp_dirname.replace("_bitetheballot_backup", "", 1)
            new_filename = "{0}_{1}".format(timestamp, filename)
            output_path = os.path.join(args.output_dir, new_filename)
            if not os.path.exists(output_path):
                try:
                    print("Downloading {0} as {1}".format(keyString, new_filename))
                    progress_bar = None
                    l.get_contents_to_filename(output_path, cb=print_progress, num_cb=100)
                    progress_bar.finish()
                except OSError as e:
                    print("Error downloading file {0}: {1}".format(keyString, e.message))
