BiteTheBallot User Analysis
===========================

Getting data
------------

The data this project works on comes from [Firebase](http://firebase.io), and
their export functionality. It assumes initially that you've downloaded the
whole thing as one `.json` file, or that you have access to an S3 bucket where
they've put an equivalent.

### Downloading the data from S3
If you need to download the data from S3, you can use the
`download_s3_bucket.py` script:

```
python download_s3_bucket.py <bucket-name> <directory-to-download-to>
```

Note, this will only download .json files in that bucket, and it'll try to
download them all, though it'll only download those it doesn't see already
in the directory you give it.

Secrets
-------

This script requires the AWS access key and secret key to be set in a file
called secret.py, this isn't checked into git to stop this being leaked.
Copy secret.py-example to secret.py and then fill in the details.

Doing everything in one go
--------------------------
If you want to do everything in one go, there's a shell script that should do
that for you. Simply copy the json file you want to convert into the repo,
create the virtualenv, and then run `main.sh`.

Splitting the data up
---------------------

The Firebase dataset is actually divided into several top-level stores which
are effectively separate. I used [jq](http://stedolan.github.io/jq)
(`brew install jq` on a Mac) to process each of these sections into smaller
json files for slightly easier handling.

## Extract the users

`cat bitetheballot.json | jq .users > bitetheballot-users.json`

## Extract the locations

`cat bitetheballot.json | jq .locations > bitetheballot-locations.json`

## Extract the priorities

`cat bitetheballot.json | jq .priorities > bitetheballot-priorities.json`

Installing the python requirements
----------------------------------
Most of the scripts are simple python files that do a bit of data munging. To
do so, they need a few packages which are described in `requirements.txt`.
The easiest way to install and use them is to create a virtualenv:

`virtualenv virtualenv-bitetheballot`

and then install them with pip:

```
source virtualenv-bitetheballot/bin/activate
pip install -r requirements.txt
```

Processing locations
--------------------
The locations in the data are just lat/lon pairs, keyed against a user id. We
want to add some info from [MapIt](http://mapit.mysociety.org), so first we
turn the JSON into a CSV:

```
python process_locations_to_csv.py bitetheballot-locations.json bitetheballot-locations.csv
```

Next, we need to run them against a MapIt instance. You might want to edit
`lookup_locations_on_mapit.py` to set an appropriate mapit host if you don't
have one locally to run.

```
python lookup_locations_on_mapit.py bitetheballot-locations.csv bitetheballot-locations-with-constituencies.csv
```

This will probably take a long time (8 hours per 100,000 locations or so), so
leave it running whilst you do the next bit.

Processing users
----------------
We need to turn the users json into a CSV that'll form the basis for our final
output. First we get the basics that are contained within the user json
itself:

```
python process_users_to_csv.py bitetheballot-users.json bitetheballot-users.csv
```

Next we add in their priorities:

```
python add_priorities_to_csv.py bitetheballot-users.csv bitetheballot-priorities.json bitetheballot-users-with-priorities.csv
```

Finally, when the locations are finished, you can combine these too:

```
python add_locations_to_csv.py bitetheballot-users-with-priorities.csv bitetheballot-locations-with-constituencies.csv bitetheballot-users-with-priorities-and-locations.csv
```

And you're done!

Extracting topics
-----------------
The list of topics and statements within them is hard-coded, but it was
intially calculated from the data. If things change and you need to regenerate
them, you can do so thusly:

```
cat bitetheballot.json | jq .topics > bitetheballot-topics.json
python produce_topics_ids.py bitetheballot-topics.json
```

You'll then need to edit the various files that hardcode these topics to use
the new ones.
