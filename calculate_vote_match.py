import json
import argparse
from collections import defaultdict
import logging

import unicodecsv
from progressbar import ProgressBar

import utils
from constants import PARTY_POSITIONS, NUM_STATEMENTS, VOTE_MATCH_FIELDS


log = logging.getLogger(__name__)
handler = logging.StreamHandler()
log.addHandler(handler)


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

        user_weight = 1
        if decision.get('weight'):
            user_weight = int(decision['weight'])  # Either 1 or 2

        log.debug(combined_id)
        log.debug("user position is: {0}".format(user_position))
        log.debug("user weight is: {0}".format(user_weight))
        log.debug("Comparing user position to parties")
        for party in user_parties:
            log.debug("party {0}".format(party))
            party_position = party_decisions_by_statement[combined_id][party]
            log.debug("party position is {0}".format(party_position))
            party_match = 0
            if user_position == party_position:
                party_match = 1
            log.debug("party match is {0}".format(party_match))
            party_weighted_match = party_match * user_weight
            log.debug("weighted match is {0}".format(party_weighted_match))
            weighted_party_matches[party][topic_id][statement_id] = party_weighted_match
    return weighted_party_matches


def user_total_weighted_party_matches_by_topic(weighted_party_matches_by_topic):
    total_party_matches = defaultdict(dict)
    log.debug("Calculating total matches by topic")
    for party, topics in weighted_party_matches_by_topic.iteritems():
        log.debug("Calculating total matches by topic for party: {0}".format(party))
        log.debug("Matches per topic are: {0}".format(topics))
        for topic, statements in topics.iteritems():
            log.debug("statements for {0} are: {1}".format(topic, statements))
            log.debug("sum of values is: {0}".format(sum(statements.itervalues())))
            total_party_matches[topic][party] = sum(statements.itervalues())
    return total_party_matches


def user_percentage_party_matches_by_topic(total_party_matches_by_topic, decisions):
    percentage_party_matches = defaultdict(dict)
    for topic, parties in total_party_matches_by_topic.iteritems():
        log.debug("totals for topic: {0} are {1}".format(topic, parties))

        # Work out what the total possible match for each party could have
        # been - e.g. if you agree on everything.
        total_possible_match_for_topic = user_total_match_score_for_topic(topic, decisions)

        log.debug("Total possible match for topic: {0}".format(total_possible_match_for_topic))

        # Then we work out what percentage each party is of that total
        for party, total_party_match in parties.iteritems():
            log.debug("Total party match for {0} is {1}".format(party, total_party_match))
            if total_possible_match_for_topic > 0:
                percentage_party_match = (float(total_party_match) / float(total_possible_match_for_topic)) * 100
            else:
                percentage_party_match = 0

            log.debug("Percentage party match for {0} is {1}".format(party, percentage_party_match))

            percentage_party_matches[topic][party] = percentage_party_match

    return percentage_party_matches


def user_total_match_score(decisions):
    """
    Calculate the total possible score, if we match all of a user's decisions
    """
    score = 0
    for decision in decisions:
        decision = utils.clean_decision(decision, decisions)
        if decision is None:
            continue

        user_position = user_position_from_decision(decision)
        if user_position is None:
            continue

        user_weight = 1
        if decision.get('weight'):
            user_weight = int(decision['weight'])  # Either 1 or 2

        score += user_weight
    return score


def user_total_match_score_for_topic(topic, decisions):
    """
    Calculate the total possible score for a single topic, if we match all of
    a user's decisions.
    """
    score = 0
    for decision in decisions:
        decision = utils.clean_decision(decision, decisions)
        if decision is None:
            continue

        user_position = user_position_from_decision(decision)
        if user_position is None:
            continue

        topic_id = decision['topic']
        if topic_id == topic:
            user_weight = 1
            if decision.get('weight'):
                user_weight = int(decision['weight'])  # Either 1 or 2
            score += user_weight
    return score


def user_percentage_party_matches(user_parties, total_possible_match, total_party_matches_by_topic):
    """
    Calculate the percentage by which the user matches the party overall, from
    all of their individual answers.
    """
    percentage_party_matches = {}
    log.debug(total_party_matches_by_topic)
    log.debug("total possible match score is: {0}".format(total_possible_match))
    for party in user_parties:
        log.debug("Calcuating percentage match for {0}".format(party))
        # Calculate the total match for this party over all the topics
        sum_total_matches = 0
        for topic, parties in total_party_matches_by_topic.iteritems():
            log.debug("on topic {0} - total matches are: {1}".format(topic, parties))
            log.debug("Total sum for this party is: {0}".format(parties[party]))
            sum_total_matches += parties[party]
        log.debug("Sum of all matches is {0}".format(sum_total_matches))
        if total_possible_match > 0:
            percentage_party_matches[party] = (float(sum_total_matches) / float(total_possible_match)) * 100
        else:
            percentage_party_matches[party] = 0
        log.debug("Percentage match is: {0}".format(percentage_party_matches[party]))
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
    parser.add_argument('output_file', type=str, help="Output CSV file")
    parser.add_argument('--verbosity', type=int)
    args = parser.parse_args()

    if args.verbosity == 3:
        log.setLevel(logging.DEBUG)
    elif args.verbosity == 2:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.ERROR)

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

    rows = []
    users = json.load(args.users_input_file)
    # Loop over every user
    log.info("Processing {0} users".format(len(users)))
    progress_bar = ProgressBar(len(users.items()))
    progress_bar.start()
    count = 0

    for user_id, user in users.items():
        count += 1
        progress_bar.update(count)

        # Some user values are not real values, skip those
        if user == "false":
            continue

        # Instantiate the row
        row = {
            'user_id': user_id,
        }
        # Work out their nation
        if user.get('nation'):
            user_nation = user['nation']['slug']
        else:
            # Assume england
            user_nation = 'eng'
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
            log.debug("Weighted party matches by topic are: {0}".format(weighted_party_matches_by_topic))
            # Total those up by topic
            total_party_matches_by_topic = user_total_weighted_party_matches_by_topic(weighted_party_matches_by_topic)
            # Then work out percentages by topic
            log.debug("Total party matches are: {0}".format(total_party_matches_by_topic))
            percentage_party_matches_by_topic = user_percentage_party_matches_by_topic(
                total_party_matches_by_topic,
                user['decisions']
            )
            log.debug("Percentage party matches are: {0}".format(percentage_party_matches_by_topic))
            # Then calculate the overall
            # We need to know what the total possible match score a user could
            # have is. e.g. if they answered 10 questions, each with a weight
            # of 2, then their overall match score is out of 20.
            total_possible_match_score = user_total_match_score(user['decisions'])
            overall_party_matches = user_percentage_party_matches(
                user_parties,
                total_possible_match_score,
                total_party_matches_by_topic
            )
            log.debug("Overall party matches are: {0}".format(overall_party_matches))

            # Created flattened dictionaries to save to the CSV row
            flattened_percentage_party_matches_by_topic = flatten_percentage_party_matches_by_topic(percentage_party_matches_by_topic)
            row.update(flattened_percentage_party_matches_by_topic)
            row.update(overall_party_matches)
            rows.append(row)

    progress_bar.finish()

    # Write everything out to the CSV file - this will add a lot of columns!
    log.info("Saving")
    output_fields = ['user_id'] + list(VOTE_MATCH_FIELDS)
    with open(args.output_file, 'wb') as f:
        writer = unicodecsv.DictWriter(f, output_fields)
        writer.writeheader()
        writer.writerows(rows)
