import json
import argparse
from collections import defaultdict

import unicodecsv
from progressbar import ProgressBar

import utils
from constants import PARTY_POSITIONS


def statements_by_topic(party_positions):
    """
    Get a dict of all of the statements for each topic, by topic id.
    """

    statements = defaultdict(list)
    for topic in party_positions.keys():
        topic_id, statement_id = topic.split("_")
        statements[topic_id].append(statement_id)
    return statements


def party_positions_by_statement(topics):
    """
    Get a dict of the positions of each party on each topic, by combined topic
    and statement id.

    Note: assumes that for the UK-wide parties, their positions are the same
    across England, Scotland and Wales.

    Note: Not used in the current code because the topics json from any given
    dump of the data doesn't include topics that have been removed from the
    app, so you need to compare the output from this to the PARTY_POSITIONS
    constant in constants.py and update things.
    """
    positions = {}
    for topic_id, topic in topics.items():
        for statement_id, statement in topic['statements'].items():
            combined_id = "{0}_{1}".format(topic_id, statement_id)
            # Start with the English positions
            positions[combined_id] = statement['eng']['matrix']['position']
            # Add the SNP's
            positions[combined_id]['snp'] = statement['scot']['matrix']['position']['snp']
            # Add Plaid's
            positions[combined_id]['plcym'] = statement['wales']['matrix']['position']['plcym']
    return positions


def user_position_from_decision(decision):
    """
    Return a user's position for a given decision, as an integer.

    If position is 9, it is normalised to None.
    """
    user_position = None
    if int(decision['position']) in (0, 1):
        user_position = int(decision['position'])
    return user_position


def user_weighted_party_matches_by_party_topic_statement(decisions, user_parties, party_decisions_by_statement):
    """
    Get a of weighted party matches against every statement in each topic for
    a user.

    Note: only returns weighted matches for those statements where the user
    actually made a decision
    """
    weighted_party_matches = {}
    for party in user_parties:
        weighted_party_matches[party] = defaultdict(defaultdict)
    for decision in decisions:
        decision = utils.clean_decision(decision, decisions)
        if decision is None:
            continue

        topic_id = decision['topic']
        statement_id = decision['statement']
        combined_id = "{0}_{1}".format(topic_id, statement_id)

        user_position = user_position_from_decision(decision)
        if user_position is None:
            continue

        user_weight = int(decision['weight'])  # Either 1 or 2

        print combined_id
        print "user position is: {0}".format(user_position)
        print "user weight is: {0}".format(user_weight)
        print "Comparing user position to parties"
        for party in user_parties:
            print "party {0}".format(party)
            party_position = party_decisions_by_statement[combined_id][party]
            print "party position is {0}".format(party_position)
            party_match = 0
            if user_position == party_position:
                party_match = 1
            print "party match is {0}".format(party_match)
            party_weighted_match = party_match * user_weight
            print "weighted match is {0}".format(party_weighted_match)
            weighted_party_matches[party][topic_id][statement_id] = party_weighted_match
    return weighted_party_matches


def user_total_weighted_party_matches_by_topic(weighted_party_matches_by_topic):
    total_party_matches = defaultdict(dict)
    print "Calculating total matches by topic"
    for party, topics in weighted_party_matches_by_topic.iteritems():
        print "Calculating total matches by topic for party: {0}".format(party)
        print "Matches per topic are: {0}".format(topics)
        for topic, statements in topics.iteritems():
            print "statements for {0} are: {1}".format(topic, statements)
            print "sum of values is: {0}".format(sum(statements.itervalues()))
            total_party_matches[topic][party] = sum(statements.itervalues())
    return total_party_matches


def user_percentage_party_matches_by_topic(total_party_matches_by_topic):
    percentage_party_matches = defaultdict(dict)
    for topic, parties in total_party_matches_by_topic.iteritems():
        print "totals for topic: {0} are {1}".format(topic, parties)
        total_party_matches_sum = sum(parties.itervalues())
        print "Sum of all party matches: {0}".format(total_party_matches_sum)
        # Then we work out what percentage each party is of that total
        for party, total_party_match in parties.iteritems():
            print "Total party match for {0} is {1}".format(party, total_party_match)
            percentage_party_match = (float(total_party_match) / float(total_party_matches_sum)) * 100
            print "Percentage party match for {0} is {1}".format(party, percentage_party_match)
            percentage_party_matches[topic][party] = percentage_party_match
    return percentage_party_matches


def user_percentage_party_matches(user_parties, num_topics, total_party_matches_by_topic):
    """
    Calculate the percentage by which the user matches the party overall, from
    all of their individual answers.
    """
    percentage_party_matches = {}
    print total_party_matches_by_topic
    print "total topics are: {0}".format(num_topics)
    for party in user_parties:
        print "Calcuating percentage match for {0}".format(party)
        # Calculate the total match for this party over all the topics
        sum_total_matches = 0
        for topic, parties in total_party_matches_by_topic.iteritems():
            print "on topic {0} - total matches are: {1}".format(topic, parties)
            print "Total sum for this party is: {0}".format(parties[party])
            sum_total_matches += parties[party]
        print "Sum of all matches is {0}".format(sum_total_matches)
        percentage_party_matches[party] = (float(sum_total_matches) / float(num_topics)) * 100
        print "Percentage match is: {0}".format(percentage_party_matches[party])
    return percentage_party_matches


def flatten_percentage_party_matches_by_topic(percentage_party_matches_by_topic):
    output = {}
    for topic, parties in percentage_party_matches_by_topic.iteritems():
        for party in parties:
            flattened_key = "{0}_{1}".format(topic, party)
            output[flattened_key] = parties[party]
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Calculates the percentage match for each person, for each topic, against each applicable party for their nation.")
    parser.add_argument(
        'users_input_file',
        type=argparse.FileType('r'),
        help="Input bitetheballot.json users file"
    )
    parser.add_argument(
        'output_file',
        type=str,
        help="Output CSV file"
    )
    args = parser.parse_args()

    # These were parsed from the original json file but are hard-coded here
    # for the sake of simplicity.
    # Which parties are available in which countries:
    UK_PARTIES = ('conservative', 'labour', 'lib', 'ukip', 'green')
    ENGLAND_PARTIES = UK_PARTIES
    SCOTLAND_PARTIES = UK_PARTIES + ('snp',)
    WALES_PARTIES = UK_PARTIES + ('plcym',)
    ALL_PARTIES = UK_PARTIES + ('snp', 'plcym')
    PARTIES_BY_COUNTRY = {
        'eng': ENGLAND_PARTIES,
        'scot': SCOTLAND_PARTIES,
        'wales': WALES_PARTIES,
    }

    # Build a list of all the statements by topic. We use the PARTY_POSITIONS
    # dict for this because its keys are a handy list of them all.
    STATEMENTS_BY_TOPIC = statements_by_topic(PARTY_POSITIONS)
    NUM_TOPICS = len(PARTY_POSITIONS.keys())

    rows = []
    users = json.load(args.users_input_file)
    # Loop over every user
    print "Processing {0} users".format(len(users))
    progress_bar = ProgressBar(len(users))
    #progress_bar.start()

    for user_id, user in users.items():
        # Instantiate the row
        row = {
            'user_id': user_id,
        }
        # Work out their nation
        user_nation = user['nation']['slug']
        # Work out which parties they should be compared against
        user_parties = PARTIES_BY_COUNTRY[user_nation]
        # Loop over every decision they made and work out how they match
        if user.get('decisions') is not None:
            # Get the weighted party matches for each statement
            weighted_party_matches_by_topic = user_weighted_party_matches_by_party_topic_statement(
                user['decisions'],
                user_parties,
                PARTY_POSITIONS
            )
            print "Weighted party matches by topic are: {0}".format(weighted_party_matches_by_topic)
            # Total those up by topic
            total_party_matches_by_topic = user_total_weighted_party_matches_by_topic(weighted_party_matches_by_topic)
            # Then work out percentages by topic
            print "Total party matches are: {0}".format(total_party_matches_by_topic)
            percentage_party_matches_by_topic = user_percentage_party_matches_by_topic(total_party_matches_by_topic)
            print "Percentage party matches are: {0}".format(percentage_party_matches_by_topic)
            # Then calculate the overall
            overall_party_matches = user_percentage_party_matches(
                user_parties,
                NUM_TOPICS,
                total_party_matches_by_topic
            )
            print "Overall party matches are: {0}".format(overall_party_matches)

            # Created flattened dictionaries to save to the CSV row
            flattened_percentage_party_matches_by_topic = flatten_percentage_party_matches_by_topic(percentage_party_matches_by_topic)
            row.update(flattened_percentage_party_matches_by_topic)
            row.update(overall_party_matches)
            rows.append(row)
            #progress_bar.update(1)

    #progress_bar.finish()

    # Write everything out to the CSV file - this will add a lot of columns!
    topic_party_match_columns = []
    for topic in STATEMENTS_BY_TOPIC:
        for party in ALL_PARTIES:
            column_name = "{0}_{1}".format(topic, party)
            topic_party_match_columns.append(column_name)

    fields = ['user_id'] + list(topic_party_match_columns) + list(ALL_PARTIES)

    with open(args.output_file, 'wb') as f:
        writer = unicodecsv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)